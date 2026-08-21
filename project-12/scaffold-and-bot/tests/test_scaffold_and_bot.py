import os
import subprocess
from bot.chord_generator import generate_chord_chart
from bot.main import simulate_button_click

def test_cli_exit_code_success(tmp_path):
    cmd = ["node", "cli/bin/scaffold.js", "init", str(tmp_path / "test-app"), "--template", "react"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert os.path.exists(tmp_path / "test-app" / "package.json")

def test_cli_exit_code_failure_existing_dir(tmp_path):
    target = tmp_path / "existing-dir"
    os.makedirs(target, exist_ok=True)
    cmd = ["node", "cli/bin/scaffold.js", "init", str(target), "--template", "react"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1 # must fail with exit code 1

def test_chord_image_generation(tmp_path):
    out_file = str(tmp_path / "test_chord_C.png")
    chart_path = generate_chord_chart("C", out_file)
    assert os.path.exists(chart_path)
    assert os.path.getsize(chart_path) > 1000

def test_bot_button_ack_speed():
    res = simulate_button_click("G")
    assert res["ack_ms"] < 3000 # Under 3 seconds
    assert res["chord"] == "G"
    assert os.path.exists(res["chart_path"])
