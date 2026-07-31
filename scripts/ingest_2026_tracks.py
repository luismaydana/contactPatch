import csv
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_tumftm_to_centerline import convert

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "tracks"
URL = "https://raw.githubusercontent.com/TUMFTM/racetrack-database/master/tracks/{}.csv"

TRACKS = [
    ("Shanghai", "shanghai", 5451),
    ("Spielberg", "spielberg", 4318),
    ("Silverstone", "silverstone", 5891),
    ("Spa", "spa", 7004),
    ("Budapest", "budapest", 4381),
    ("Zandvoort", "zandvoort", 4259),
    ("Austin", "austin", 5513),
    ("MexicoCity", "mexicocity", 4304),
    ("SaoPaulo", "saopaulo", 4309),
]


def total_length(dst):
    with open(dst) as f:
        last = None
        for row in csv.DictReader(f):
            last = row
    return float(last["s_arc"])


def main():
    print(f"{'track':<13}{'points':>8}{'len_m':>10}{'official':>10}{'delta%':>8}  verdict")
    for name, d, official in TRACKS:
        raw = RAW_DIR / f"_raw_{name}.csv"
        dst = ROOT / "data" / "tracks" / d / "centerline.csv"
        try:
            data = urllib.request.urlopen(URL.format(name), timeout=60).read()
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(data)
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                convert(raw, dst)
            n = sum(1 for _ in open(dst)) - 1
            length = total_length(dst)
            delta = 100.0 * (length - official) / official
            verdict = "PASS" if abs(delta) <= 2.0 else "FLAG"
            print(f"{d:<13}{n:>8}{length:>10.1f}{official:>10}{delta:>+8.2f}  {verdict}")
        except Exception as e:
            print(f"{d:<13}  ERROR: {e}")
        finally:
            if raw.exists():
                raw.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
