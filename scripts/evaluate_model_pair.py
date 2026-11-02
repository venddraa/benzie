"""Uji dua model secara berurutan pada sesi yang sama; tanpa mengubah desktop."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median
import sys

from benzie.config import default_data_directory
from benzie.inference.server import RuntimeStartError, ServerConfig
from evaluate_local_model import SUITE, main as evaluate

CONTROLS = ("suite_sha256", "system_prompt_sha256", "runtime_sha256", "context_size",
            "threads", "max_tokens", "temperature", "thinking", "sampling", "python", "platform")


def summarize_report(report, expected_ids):
    cases = report["cases"]
    if (report.get("complete") is not True or report.get("selected_cases") != len(expected_ids)
            or [case["id"] for case in cases] != expected_ids
            or any(case.get("status") != "generated" for case in cases)
            or any(key not in report for key in CONTROLS)):
        raise ValueError("Laporan tidak lengkap atau kasus tidak sesuai.")
    return {
        "median_load_seconds": median(case["load_seconds"] for case in cases),
        "median_ttft_seconds": median(case["ttft_seconds"] for case in cases),
        "median_decode_tokens_per_second": median(case["decode_tokens_per_second"] for case in cases),
        "max_peak_rss_bytes": max(case["peak_rss_bytes"] for case in cases),
    }


def run_pair(binary, models, output, *, pairs=1, limit=10, evaluator=evaluate):
    for model in models:
        ServerConfig(binary, model).command()
    if models[0].resolve() == models[1].resolve():
        raise ValueError("Pilih dua file model berbeda.")
    suite = json.loads(SUITE.read_text(encoding="utf-8"))
    expected_ids = [case["id"] for case in suite["cases"][:limit]]
    output.mkdir(parents=True, exist_ok=False)  # Jangan timpa eksperimen sebelumnya.
    summary = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
               "complete": False, "pairs": pairs, "cases_per_run": limit, "runs": [],
               "quality_status": "manual_review_required", "controls": None}
    code = 1
    model_hashes = {}
    try:
        for pair in range(pairs):
            order = (0, 1) if pair % 2 == 0 else (1, 0)
            for index in order:
                label = "a" if index == 0 else "b"
                filename = f"pair-{pair + 1}-{label}.json"
                row = {"pair": pair + 1, "model": label, "report": filename}
                summary["runs"].append(row)
                print(f"Pasangan {pair + 1}/{pairs}, model {label.upper()} dimulai", flush=True)
                result = evaluator(["--binary", str(binary), "--model", str(models[index]),
                                    "--limit", str(limit), "--output", str(output / filename)])
                row["exit_code"] = result
                if result != 0:
                    code = result
                    return code
                report = json.loads((output / filename).read_text(encoding="utf-8"))
                metrics = summarize_report(report, expected_ids)
                controls = {key: report[key] for key in CONTROLS}
                if summary["controls"] is None:
                    summary["controls"] = controls
                elif summary["controls"] != controls:
                    raise ValueError("Parameter atau environment berubah antar-run.")
                digest = report["model_sha256"]
                if label in model_hashes and model_hashes[label] != digest:
                    raise ValueError("Artefak model berubah antar-run.")
                model_hashes[label] = digest
                row.update(model_file=report["model_file"], model_sha256=digest,
                           system_memory_before=report["system_memory_before"], metrics=metrics)
        summary["complete"] = True
        code = 0
        return code
    except KeyboardInterrupt:
        code = 130
        raise
    finally:
        summary["exit_code"] = code
        with (output / "summary.json").open("x", encoding="utf-8") as stream:
            json.dump(summary, stream, ensure_ascii=False, indent=2, allow_nan=False)
        print(f"Ringkasan pasangan: {output / 'summary.json'}", flush=True)


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=root / ".tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server")
    parser.add_argument("--model-a", type=Path, default=default_data_directory() / "models/Qwen3-0.6B-Q8_0.gguf")
    parser.add_argument("--model-b", type=Path, default=default_data_directory() / "models/Qwen3-1.7B-Q8_0.gguf")
    parser.add_argument("--pairs", type=int, default=1, help="pasangan A/B, 1–3; urutan kedua B/A")
    parser.add_argument("--limit", type=int, default=10, help="kasus per model, 1–10")
    parser.add_argument("--output-dir", type=Path, default=root / "data" / f"paired-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}")
    args = parser.parse_args(argv)
    if not 1 <= args.pairs <= 3 or not 1 <= args.limit <= 10:
        parser.error("--pairs harus 1–3 dan --limit 1–10.")
    print("Tutup Benzie/aplikasi berat. Satu model berjalan setiap saat; kondisi OS tidak diubah.", flush=True)
    try:
        code = run_pair(args.binary.expanduser().resolve(),
                        [args.model_a.expanduser().resolve(), args.model_b.expanduser().resolve()],
                        args.output_dir.expanduser().resolve(), pairs=args.pairs, limit=args.limit)
        print("Run selesai; periksa complete dan RAM/swap pada ringkasan. Kualitas tetap dinilai manual."
              if code == 0 else "Eksperimen dihentikan pada run gagal; jangan anggap perbandingan lengkap.")
        return code
    except (RuntimeStartError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Uji berpasangan gagal ({type(error).__name__}); periksa artefak/laporan.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Uji dibatalkan. Periksa laporan parsial; jangan gabungkan sebagai hasil lengkap.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
