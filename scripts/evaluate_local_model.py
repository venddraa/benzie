"""Evaluasi lokal dengan prompt sintetis tetap; simpan jawaban untuk review manual.

Tidak membaca history, mengunduh model, atau memberi skor dengan cloud/judge LLM.
"""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

from benzie.config import default_data_directory
from benzie.core.model_settings import SettingsError, load_settings
from benzie.core.prompts import SYSTEM_PROMPT
from benzie.inference.benchmark import process_resources, system_memory
from benzie.inference.engine import InferenceError, LlamaServerEngine
from benzie.inference.server import RuntimeStartError, ServerConfig

SUITE = Path(__file__).with_name("evaluation_cases.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_case(case, engine, *, resource_reader=process_resources):
    row = {"id": case["id"], "prompt": case["prompt"], "history": case.get("history", []),
           "criteria": case["criteria"], "status": "error", "answer": "", "manual_score": None}
    try:
        started = time.perf_counter()
        engine.start(timeout=120)
        row["load_seconds"] = time.perf_counter() - started
        first_text = None
        tokens = speed = None
        generation_started = time.perf_counter()
        with closing(engine.generate_stream(
            case["prompt"], system_prompt=SYSTEM_PROMPT, history=case.get("history", []),
            max_tokens=256, temperature=0.0, timeout=60,
        )) as events:
            for event in events:
                if event.text:
                    if first_text is None:
                        first_text = time.perf_counter()
                    row["answer"] += event.text
                if event.completion_tokens is not None:
                    tokens = event.completion_tokens
                if event.decode_tokens_per_second is not None:
                    speed = event.decode_tokens_per_second
        row["generation_seconds"] = time.perf_counter() - generation_started
        if first_text is None or tokens is None or tokens <= 0 or speed is None:
            raise InferenceError("Statistik generation tidak lengkap.")
        row.update(ttft_seconds=first_text - generation_started, completion_tokens=tokens,
                   decode_tokens_per_second=speed, possibly_token_limited=tokens >= 256)
        pid = engine.process_id
        if pid is None:
            raise InferenceError("Runtime berhenti sebelum resource diukur.")
        row.update(resource_reader(pid))
        row["status"] = "generated"  # Bukan berarti kualitas jawabannya lulus.
    except (InferenceError, RuntimeStartError, OSError, ValueError) as error:
        row["error_type"] = type(error).__name__  # Tanpa raw native error/path.
    finally:
        engine.close()
    return row


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path, default=default_data_directory() / "model-settings.json")
    parser.add_argument("--binary", type=Path, help="override binary; harus bersama --model")
    parser.add_argument("--model", type=Path, help="override GGUF lokal; tidak mengubah pilihan desktop")
    parser.add_argument("--limit", type=int, default=10, help="jumlah kasus awal, 1–10")
    parser.add_argument("--output", type=Path, default=root / "data" / f"evaluation-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.json")
    args = parser.parse_args(argv)
    if (args.binary is None) != (args.model is None) or not 1 <= args.limit <= 10:
        parser.error("Berikan --binary/--model bersama; --limit harus 1–10.")
    try:
        if args.model is not None:
            config = ServerConfig(args.binary.expanduser().resolve(), args.model.expanduser().resolve())
        else:
            settings = load_settings(args.settings)
            if settings is None:
                raise SettingsError("Pilih model melalui Benzie atau berikan --binary dan --model.")
            config = settings.server_config()
        config.command()
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        report = {
            "schema_version": 1, "suite_id": suite["suite_id"], "suite_sha256": sha256_file(SUITE),
            "created_at": datetime.now(timezone.utc).isoformat(), "complete": False,
            "system_prompt": SYSTEM_PROMPT, "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            "model_file": config.model.name, "model_bytes": config.model.stat().st_size,
            "model_sha256": sha256_file(config.model), "runtime_sha256": sha256_file(config.executable),
            "context_size": config.context_size, "threads": config.threads,
            "max_tokens": 256, "temperature": 0.0, "thinking": False,
            "sampling": "restart_per_case_os_cache_not_cleared", "python": platform.python_version(),
            "platform": platform.platform(), "system_memory_before": system_memory(),
            "selected_cases": args.limit, "cases": [], "quality_status": "awaiting_manual_review",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Eksklusif: laporan lama tidak boleh tertimpa. Simpan progres jika terinterupsi.
        with args.output.open("x", encoding="utf-8") as stream:
            try:
                for case in suite["cases"][:args.limit]:
                    row = evaluate_case(case, LlamaServerEngine(config))
                    report["cases"].append(row)
                    print(f"{row['id']}: {row['status']}", flush=True)
                report["complete"] = True
            finally:
                json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        failures = sum(row["status"] != "generated" for row in report["cases"])
        print(f"Laporan sintetis: {args.output}\nKasus gagal: {failures}; kualitas menunggu review manual.")
        return 1 if failures else 0
    except (SettingsError, RuntimeStartError, InferenceError, OSError, ValueError) as error:
        print(f"Evaluasi gagal ({type(error).__name__}); periksa konfigurasi dan lokasi output.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Evaluasi dibatalkan; runtime ditutup dan progres laporan disimpan jika sudah dimulai.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
