#!/usr/bin/env bash
# Project 11: Phaser 3 平台跳躍遊戲 Rooftop Dash 課堂遙控器
# 轉發至 rooftop-dash/demo.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/rooftop-dash/demo.sh" "$@"
