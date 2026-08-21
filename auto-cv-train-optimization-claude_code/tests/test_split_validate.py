from autocv.split import validate_label_file


def test_valid_label(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("0 0.5 0.5 0.2 0.2\n1 0.1 0.1 0.05 0.05\n")
    errors, cids, n = validate_label_file(f)
    assert errors == []
    assert cids == [0, 1]
    assert n == 2


def test_missing_file(tmp_path):
    errors, cids, n = validate_label_file(tmp_path / "nope.txt")
    assert len(errors) == 1
    assert n == 0


def test_out_of_range_and_bad_fields(tmp_path):
    f = tmp_path / "b.txt"
    f.write_text("0 1.5 0.5 0.2 0.2\n0 0.5 0.5\n-1 0.5 0.5 0.2 0.2\n")
    errors, cids, n = validate_label_file(f)
    assert any("超出" in e for e in errors)
    assert any("欄位數" in e for e in errors)
    assert any("為負" in e for e in errors)
