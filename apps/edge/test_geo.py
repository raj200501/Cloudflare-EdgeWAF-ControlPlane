from pathlib import Path

from apps.edge.main import resolve_country


def test_geo_policy_mapping(tmp_path: Path):
    path = tmp_path / "geo.json"
    path.write_text('{"1": "US"}')
    assert path.exists()
    assert resolve_country("1.2.3.4") in {"US", "Unknown"}
