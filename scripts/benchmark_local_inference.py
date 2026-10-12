"""Benchmark tiga restart runtime dengan prompt sintetis; hanya simpan metrik."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from benzie.config import default_data_directory
from benzie.core.prompts import SYSTEM_PROMPT
from benzie.inference.benchmark import process_resources, summarize, system_memory
from benzie.inference.engine import InferenceError, LlamaServerEngine
from benzie.inference.server import RuntimeStartError, ServerConfig

PROMPT = "Jelaskan manfaat berjalan kaki bagi rutinitas sehari-hari dalam 12 poin singkat. Gunakan Bahasa Indonesia."


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=root / ".tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server")
    parser.add_argument("--model", type=Path, default=default_data_directory() / "models/Qwen3-0.6B-Q8_0.gguf")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", type=Path, default=root / "data" / f"benchmark-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.json")
    args = parser.parse_args()
    if not 1 <= args.runs <= 10:
        parser.error("--runs harus antara 1 dan 10")
    args.binary = args.binary.expanduser().resolve()
    args.model = args.model.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    config = ServerConfig(args.binary, args.model, port=args.port, threads=args.threads)
    runs = []
    try:
        config.command()  # Validasi lokal sebelum menjalankan binary.
        version = subprocess.run([str(args.binary.resolve()), "--version"], capture_output=True, text=True, timeout=10, check=True)
        runtime_version = (version.stdout + version.stderr).strip()
        for index in range(args.runs):
            engine = LlamaServerEngine(config)
            try:
                memory_before = system_memory()
                started = time.perf_counter()
                engine.start()
                load_seconds = time.perf_counter() - started
                first_text = None
                tokens = None
                speed = None
                generation_started = time.perf_counter()
                with closing(engine.generate_stream(PROMPT, system_prompt=SYSTEM_PROMPT)) as events:
                    for event in events:
                        if event.text and first_text is None:
                            first_text = time.perf_counter()
                        if event.completion_tokens is not None:
                            tokens = event.completion_tokens
                        if event.decode_tokens_per_second is not None:
                            speed = event.decode_tokens_per_second
                generation_seconds = time.perf_counter() - generation_started
                if first_text is None or tokens is None or tokens <= 0 or speed is None:
                    raise InferenceError("Statistik generation tidak lengkap; benchmark tidak dapat dihitung.")
                pid = engine.process_id
                if pid is None:
                    raise InferenceError("Runtime berhenti sebelum pengukuran resource.")
                resources = process_resources(pid)
                observed_seconds = time.perf_counter() - started
                row = {
                    "run": index + 1, "load_seconds": load_seconds,
                    "ttft_seconds": first_text - generation_started,
                    "generation_seconds": generation_seconds,
                    "completion_tokens": tokens, "decode_tokens_per_second": speed,
                    "system_memory_before": memory_before,
                    **resources, "average_cpu_percent": 100 * resources["cpu_seconds"] / observed_seconds,
                }
                runs.append(row)
                print(f"Run {index + 1}: load {load_seconds:.2f}s | TTFT {row['ttft_seconds']:.3f}s | decode {speed:.2f} tok/s | peak RSS {resources['peak_rss_bytes'] / 1024**2:.1f} MiB", flush=True)
            finally:
                engine.close()
        report = {
            "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "runtime_version": runtime_version, "model_file": args.model.name,
            "model_bytes": args.model.stat().st_size, "platform": platform.platform(),
            "python": platform.python_version(), "context_size": config.context_size,
            "logical_cpu_count": os.cpu_count(),
            "cpu_model": next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), "unknown"),
            "threads": config.threads, "max_tokens": 128, "temperature": 0.7,
            "prompt_id": "walking-benefits-id-v1", "sampling": "process_restart_each_run_os_cache_not_cleared",
            "runs": runs, "summary": summarize(runs),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        print(json.dumps(report["summary"], indent=2))
        print(f"Benchmark PASS; laporan metrik: {args.output}")
    except (InferenceError, RuntimeStartError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Benchmark gagal: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Benchmark dibatalkan; cleanup dijalankan.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
