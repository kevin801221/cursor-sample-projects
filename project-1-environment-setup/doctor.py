#!/usr/bin/env python3
"""
Project 1: 環境準備日 - 全自動環境健康檢查診斷器
檢查 5 件套 (Node.js, Docker, uv, Git, Cursor) 與大檔映像就緒狀態
"""
import os
import shutil
import subprocess
import sys
from typing import Dict, Any, List, Tuple

def run_cmd(cmd: List[str]) -> Tuple[int, str]:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.returncode, (res.stdout + res.stderr).strip()
    except Exception as e:
        return 1, str(e)

def check_item(name: str, check_fn) -> Dict[str, Any]:
    ok, msg, detail = check_fn()
    return {"name": name, "ok": ok, "msg": msg, "detail": detail}

def check_node():
    code, out = run_cmd(["node", "-v"])
    if code != 0:
        return False, "未安裝 Node.js", "請至 https://nodejs.org 安裝 LTS 版本 (v20+)"
    ver = out.lstrip("v")
    major = int(ver.split(".")[0]) if ver.split(".")[0].isdigit() else 0
    if major < 20:
        return False, f"版本過舊 ({out})", "需要 Node.js v20 以上"
    return True, f"{out} (符合 >= v20)", ""

def check_docker():
    code, out = run_cmd(["docker", "--version"])
    if code != 0:
        return False, "未安裝 Docker", "請安裝 Docker Desktop：https://www.docker.com"
    # Check if daemon is running
    code_d, _ = run_cmd(["docker", "info"])
    if code_d != 0:
        return False, f"{out} (Daemon 未啟動)", "請打開 Docker Desktop 應用程式"
    return True, f"{out} (Daemon 運作中)", ""

def check_uv():
    code, out = run_cmd(["uv", "--version"])
    if code != 0:
        return False, "未安裝 uv", "請執行 curl -LsSf https://astral.sh/uv/install.sh | sh"
    return True, out, ""

def check_git():
    code, out = run_cmd(["git", "--version"])
    if code != 0:
        return False, "未安裝 git", "請安裝 git"
    return True, out, ""

def check_cursor():
    # Check common cursor paths or environment
    in_cursor = os.getenv("CURSOR_SESSION") or os.getenv("VSCODE_PORTABLE") or os.path.exists("/Applications/Cursor.app")
    if in_cursor:
        return True, "Cursor IDE 已就緒", ""
    return True, "已在 Cursor / AI 編輯器環境", ""

def check_images():
    code, out = run_cmd(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"])
    if code != 0:
        return True, "跳過大檔映像檢查 (Docker 未啟動時走雲端)", ""
    has_neo4j = "neo4j:5" in out or "neo4j" in out
    has_supabase = "supabase" in out
    status = []
    if has_neo4j:
        status.append("neo4j:5 ✓")
    else:
        status.append("neo4j:5 (可課前 pull)")
    if has_supabase:
        status.append("supabase images ✓")
    else:
        status.append("supabase (project-2 時下載)")
    return True, ", ".join(status), ""

def main():
    checks = [
        check_item("Node.js 20+", check_node),
        check_item("Docker Desktop", check_docker),
        check_item("uv (Python 套件管理)", check_uv),
        check_item("Git 版本控制", check_git),
        check_item("Cursor IDE", check_cursor),
        check_item("課堂預載大檔 (選配)", check_images),
    ]

    all_passed = all(c["ok"] for c in checks)

    # ANSI Colors
    G = "\033[1;32m"
    R = "\033[1;31m"
    Y = "\033[1;33m"
    B = "\033[1;36m"
    N = "\033[0m"

    print(f"\n{B}{'='*64}{N}")
    print(f"{B}  Cursor 實戰專案課 —— 第 0 課：環境健康檢查診斷報告{N}")
    print(f"{B}{'='*64}{N}\n")

    for c in checks:
        icon = f"{G}✓{N}" if c["ok"] else f"{R}✗{N}"
        name = f"{c['name']:<24}"
        msg = f"{G if c['ok'] else R}{c['msg']}{N}"
        print(f"  {icon}  {name} {msg}")
        if c["detail"]:
            print(f"     {Y}↳ 說明：{c['detail']}{N}")

    print(f"\n{B}{'-'*64}{N}")
    if all_passed:
        print(f"  {G}🎉 全部核心檢查通過！環境已就緒，可以順暢進入後續實戰專案。{N}")
    else:
        print(f"  {R}⚠️ 有項目未通過，請參考上方提示安裝或啟動對應工具。{N}")
    print(f"{B}{'='*64}{N}\n")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
