from apps.edge.main import GeoPolicy
from pathlib import Path


def test_geo_policy_mapping(tmp_path: Path):
    data = {"1": "US"}
    path = tmp_path / "geo.json"
    path.write_text("{\"1\": \"US\"}")
    policy = GeoPolicy.from_json(path)
    assert policy.resolve_country("1.2.3.4") == "US"
    assert policy.allow("US") is True
    policy.denylist.add("US")
    assert policy.allow("US") is False
