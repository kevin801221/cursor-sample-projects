from autocv.device import pick_device


def test_explicit_device_passthrough():
    assert pick_device("cpu") == "cpu"
    assert pick_device("mps") == "mps"


def test_auto_returns_valid_device(monkeypatch):
    import autocv.device as d

    monkeypatch.setattr(d, "_mps_available", lambda: False)
    monkeypatch.setattr(d, "_cuda_available", lambda: False)
    assert pick_device("auto") == "cpu"

    monkeypatch.setattr(d, "_mps_available", lambda: True)
    assert pick_device("auto") == "mps"
