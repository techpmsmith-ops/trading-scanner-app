import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_MODEL = "NeoQuasar/Kronos-mini"
DEFAULT_TOKENIZER = "NeoQuasar/Kronos-Tokenizer-2k"


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.check_call(command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install and smoke-test the optional Kronos forecasting dependency.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--tokenizer", default=DEFAULT_TOKENIZER)
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    kronos_root = repo_root / "external" / "Kronos"
    requirements = kronos_root / "requirements.txt"
    if not requirements.exists():
        raise SystemExit("external/Kronos is missing. Clone https://github.com/shiyu-coder/Kronos into external/Kronos first.")

    if not args.skip_install:
        run([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

    sys.path.insert(0, str(kronos_root))
    try:
        from model import Kronos, KronosPredictor, KronosTokenizer
    except Exception as exc:
        raise SystemExit(f"Kronos import failed: {exc}") from exc

    print(f"Loading tokenizer: {args.tokenizer}")
    tokenizer = KronosTokenizer.from_pretrained(args.tokenizer)
    print(f"Loading model: {args.model}")
    model = Kronos.from_pretrained(args.model)
    device = None if args.device == "auto" else args.device
    predictor = KronosPredictor(model, tokenizer, device=device, max_context=2048 if "mini" in args.model.lower() else 512)
    print(f"Kronos smoke test OK. Device: {predictor.device}; model: {args.model}; tokenizer: {args.tokenizer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
