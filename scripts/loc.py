from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [ROOT / "apps" / "edge", ROOT / "apps" / "dashboard", ROOT / "packages"]


def count_lines(path: Path) -> int:
    total = 0
    for file in path.rglob("*"):
        if file.is_file() and file.suffix in {".py", ".ts", ".tsx", ".js", ".json", ".css", ".md"}:
            total += sum(1 for _ in file.open("r", encoding="utf-8", errors="ignore"))
    return total


if __name__ == "__main__":
    grand = 0
    for target in TARGETS:
        loc = count_lines(target)
        grand += loc
        print(f"{target.relative_to(ROOT)}: {loc}")
    print(f"total: {grand}")
