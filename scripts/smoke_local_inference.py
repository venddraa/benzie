"""Smoke test eksplisit dengan prompt sintetis; tidak menyimpan percakapan."""

import argparse
from pathlib import Path
import sys
import time

from benzie.config import default_data_directory
from benzie.core.prompts import SYSTEM_PROMPT
from benzie.inference.engine import InferenceError, LlamaServerEngine
from benzie.inference.server import RuntimeStartError, ServerConfig


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=root / ".tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server")
    parser.add_argument("--model", type=Path, default=default_data_directory() / "models/Qwen3-0.6B-Q8_0.gguf")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    engine = LlamaServerEngine(ServerConfig(args.binary, args.model, port=args.port))
    try:
        started = time.monotonic()
        engine.start()
        print(f"Model siap setelah {time.monotonic() - started:.2f} detik", flush=True)
        answer = engine.generate("Halo Benzie. Jawab dalam Bahasa Indonesia, maksimal dua kalimat.", system_prompt=SYSTEM_PROMPT)
        print(f"Benzie: {answer}")
    except (InferenceError, RuntimeStartError, ValueError) as error:
        print(f"Smoke test gagal: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Smoke test dibatalkan.", file=sys.stderr)
        return 130
    finally:
        engine.close()
    print("Smoke test PASS; proses runtime sudah ditutup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
