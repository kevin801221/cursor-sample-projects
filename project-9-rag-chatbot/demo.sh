#!/usr/bin/env bash
# Project 9: RAG 知識庫 Chatbot 課堂遙控器
# 轉發至 rag-chatbot/demo.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/rag-chatbot/demo.sh" "$@"
