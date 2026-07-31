import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "scripts")
CACHE = os.path.join(ROOT, "data", "fastf1_cache")

FIELD = [
    ("Suzuka", 2026, 3),
    ("Melbourne", 2026, 1),
    ("Barcelona", 2026, 7),
    ("Montreal", 2026, 5),
    ("Shanghai", 2026, 2),
]
MONZA = ("Monza", 2025, "Monza")

TARGETS = {
    "Suzuka": 1.26,
    "Melbourne": 0.35,
    "Barcelona": -0.51,
    "Montreal": -1.40,
    "Shanghai": 7.38,
    "Monza": 2.90,
}
TOL_FIELD = 0.20
TOL_MONZA = 0.20
