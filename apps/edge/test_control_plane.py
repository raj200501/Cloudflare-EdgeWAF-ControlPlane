from apps.edge.control_plane import ControlPlane, WafRule


def test_snapshot_hash_and_activation():
    cp = ControlPlane()
    cp.waf_rules["1"] = WafRule(
        id="1",
        field="query",
        operator="contains",
        pattern="select",
        reason="sqli",
    )

    snap1 = cp.compile_snapshot()
    snap2 = cp.compile_snapshot()

    assert snap1.hash == snap2.hash
    assert snap1.etag.startswith('W/"')

    active = cp.activate(snap1.id)
    assert cp.active().id == active.id
