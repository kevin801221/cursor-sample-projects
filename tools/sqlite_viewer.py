#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Open a local SQLite database in a small, read-only browser UI.

No third-party packages are required. Run from the repository root:

    uv run tools/sqlite_viewer.py path/to/database.db
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
import threading
import webbrowser
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse


SQLITE_HEADER = b"SQLite format 3\x00"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
SKIP_DIRECTORIES = {
    ".git",
    ".idea",
    ".next",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}


class ViewerError(Exception):
    """An error that can safely be shown in the browser UI."""


def is_sqlite_database(path: Path) -> bool:
    """Return True only when *path* has SQLite's standard file header."""
    try:
        if not path.is_file():
            return False
        with path.open("rb") as database_file:
            return database_file.read(len(SQLITE_HEADER)) == SQLITE_HEADER
    except OSError:
        return False


def discover_databases(root: Path) -> List[Path]:
    """Find SQLite files below *root* while skipping generated dependency trees."""
    candidates: List[Path] = []
    suffixes = {".db", ".sqlite", ".sqlite3"}

    for current_root, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in SKIP_DIRECTORIES]
        current_path = Path(current_root)
        for filename in files:
            path = current_path / filename
            if path.suffix.lower() in suffixes and is_sqlite_database(path):
                candidates.append(path.resolve())

    return sorted(candidates, key=lambda item: str(item).lower())


def choose_database(root: Path) -> Path:
    """Select a discovered database, prompting only when several are present."""
    databases = discover_databases(root)
    if not databases:
        raise ViewerError(
            "找不到 SQLite 資料庫。請指定路徑，例如："
            "uv run tools/sqlite_viewer.py data/app.db"
        )
    if len(databases) == 1:
        return databases[0]
    if not sys.stdin.isatty():
        choices = "\n".join(f"  - {path.relative_to(root)}" for path in databases)
        raise ViewerError(f"找到多個資料庫，請在指令中指定其中一個：\n{choices}")

    print("找到以下 SQLite 資料庫：")
    for index, path in enumerate(databases, start=1):
        try:
            label = path.relative_to(root)
        except ValueError:
            label = path
        print(f"  {index}. {label}")

    while True:
        try:
            answer = input(f"請選擇 [1-{len(databases)}]（預設 1）：").strip() or "1"
            selected = int(answer)
            if 1 <= selected <= len(databases):
                return databases[selected - 1]
        except (EOFError, ValueError):
            pass
        print("輸入無效，請再試一次。")


def validate_database(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise ViewerError(f"找不到資料庫：{resolved}")
    if not resolved.is_file():
        raise ViewerError(f"這不是檔案：{resolved}")
    if not is_sqlite_database(resolved):
        raise ViewerError(f"檔案不是有效的 SQLite 資料庫：{resolved}")
    return resolved


def open_readonly(path: Path) -> sqlite3.Connection:
    """Open a SQLite connection that cannot mutate the database file."""
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, check_same_thread=False, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def list_objects(connection: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT name, type, sql
        FROM sqlite_schema
        WHERE type IN ('table', 'view')
          AND name NOT GLOB 'sqlite_*'
        ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name COLLATE NOCASE
        """
    ).fetchall()

    objects: List[Dict[str, Any]] = []
    for row in rows:
        count: Optional[int]
        try:
            result = connection.execute(
                f"SELECT COUNT(*) FROM {quote_identifier(row['name'])}"
            ).fetchone()
            count = int(result[0]) if result is not None else 0
        except sqlite3.Error:
            count = None
        objects.append(
            {
                "name": row["name"],
                "type": row["type"],
                "row_count": count,
                "sql": row["sql"] or "",
            }
        )
    return objects


def get_object(connection: sqlite3.Connection, name: str) -> Dict[str, Any]:
    row = connection.execute(
        """
        SELECT name, type, sql
        FROM sqlite_schema
        WHERE name = ? AND type IN ('table', 'view')
        """,
        (name,),
    ).fetchone()
    if row is None or name.startswith("sqlite_"):
        raise ViewerError(f"找不到資料表或檢視表：{name}")
    return {"name": row["name"], "type": row["type"], "sql": row["sql"] or ""}


def get_schema(connection: sqlite3.Connection, name: str) -> List[Dict[str, Any]]:
    get_object(connection, name)
    rows = connection.execute(f"PRAGMA table_info({quote_identifier(name)})").fetchall()
    return [
        {
            "position": int(row["cid"]),
            "name": row["name"],
            "type": row["type"] or "",
            "not_null": bool(row["notnull"]),
            "default": row["dflt_value"],
            "primary_key": int(row["pk"]),
        }
        for row in rows
    ]


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        # JavaScript cannot represent every SQLite 64-bit integer exactly.
        return value if abs(value) <= 9_007_199_254_740_991 else str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, bytes):
        return {"blob_bytes": len(value), "preview": value[:16].hex()}
    return str(value)


def query_object(
    connection: sqlite3.Connection,
    name: str,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    search: str = "",
) -> Dict[str, Any]:
    """Return one safe, paginated page from a whitelisted table or view."""
    db_object = get_object(connection, name)
    schema = get_schema(connection, name)
    page = max(1, int(page))
    page_size = max(1, min(MAX_PAGE_SIZE, int(page_size)))
    columns = [column["name"] for column in schema]
    identifier = quote_identifier(name)

    where_sql = ""
    parameters: List[Any] = []
    cleaned_search = search.strip()
    if cleaned_search and columns:
        predicates = [
            f"CAST({quote_identifier(column)} AS TEXT) LIKE ? ESCAPE '\\'"
            for column in columns
        ]
        where_sql = " WHERE " + " OR ".join(predicates)
        pattern = f"%{escape_like(cleaned_search)}%"
        parameters.extend([pattern] * len(columns))

    count_row = connection.execute(
        f"SELECT COUNT(*) FROM {identifier}{where_sql}", parameters
    ).fetchone()
    filtered_count = int(count_row[0]) if count_row is not None else 0
    total_pages = max(1, math.ceil(filtered_count / page_size))
    page = min(page, total_pages)
    offset = (page - 1) * page_size

    order_sql = ""
    primary_keys = sorted(
        (column for column in schema if column["primary_key"]),
        key=lambda column: column["primary_key"],
    )
    if primary_keys:
        order_sql = " ORDER BY " + ", ".join(
            quote_identifier(column["name"]) for column in primary_keys
        )

    rows = connection.execute(
        f"SELECT * FROM {identifier}{where_sql}{order_sql} LIMIT ? OFFSET ?",
        [*parameters, page_size, offset],
    ).fetchall()

    return {
        "name": name,
        "type": db_object["type"],
        "sql": db_object["sql"],
        "columns": columns,
        "schema": schema,
        "rows": [[json_value(row[column]) for column in columns] for row in rows],
        "page": page,
        "page_size": page_size,
        "filtered_count": filtered_count,
        "total_pages": total_pages,
        "search": cleaned_search,
    }


APP_HTML = r"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SQLite Viewer</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: light-dark(#f4f1eb, #111310);
      --panel: light-dark(#fffdf8, #1a1d18);
      --panel-2: light-dark(#eeebe4, #222620);
      --text: light-dark(#1f241d, #f2f5ee);
      --muted: light-dark(#667060, #aab4a3);
      --line: light-dark(#d9d5cb, #363c33);
      --accent: light-dark(#176b4d, #5ed6a4);
      --accent-soft: light-dark(#dcefe6, #183b2d);
      --danger: light-dark(#a1392e, #ff9f91);
      --shadow: 0 16px 50px light-dark(rgba(43, 51, 39, .10), rgba(0, 0, 0, .30));
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); }
    button, input, select { font: inherit; }
    button, select {
      border: 1px solid var(--line); background: var(--panel); color: var(--text);
      border-radius: 9px; padding: .55rem .75rem;
    }
    button { cursor: pointer; }
    button:hover { border-color: var(--accent); }
    button:disabled { opacity: .45; cursor: default; }
    button:focus-visible, input:focus-visible, select:focus-visible { outline: 3px solid var(--accent-soft); outline-offset: 2px; }
    .app { min-height: 100vh; display: grid; grid-template-columns: 280px minmax(0, 1fr); }
    .sidebar { border-right: 1px solid var(--line); background: var(--panel); padding: 1.25rem; }
    .brand { display: flex; align-items: center; gap: .7rem; margin-bottom: 1.4rem; }
    .mark { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 10px; background: var(--accent); color: var(--panel); font-weight: 700; }
    .brand strong { display: block; }
    .brand small { display: block; color: var(--muted); margin-top: .12rem; }
    .sidebar-title { color: var(--muted); font-size: .75rem; letter-spacing: .09em; text-transform: uppercase; margin-bottom: .55rem; }
    .object-list { display: grid; gap: .3rem; }
    .object-button { width: 100%; display: flex; justify-content: space-between; gap: .8rem; text-align: left; border-color: transparent; background: transparent; }
    .object-button[aria-current="true"] { background: var(--accent-soft); border-color: transparent; color: var(--accent); }
    .object-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .object-count { color: var(--muted); font-variant-numeric: tabular-nums; }
    .main { min-width: 0; padding: 1.5rem clamp(1rem, 3vw, 2.5rem) 2.5rem; }
    .topbar { display: flex; gap: 1rem; align-items: flex-start; justify-content: space-between; margin-bottom: 1.5rem; }
    h1 { margin: 0; font-size: clamp(1.35rem, 3vw, 2rem); font-weight: 650; letter-spacing: -.025em; }
    .db-path { color: var(--muted); margin-top: .35rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .82rem; overflow-wrap: anywhere; }
    .readonly { display: inline-flex; gap: .4rem; align-items: center; flex: 0 0 auto; border: 1px solid var(--line); border-radius: 999px; padding: .4rem .65rem; color: var(--accent); font-size: .8rem; }
    .readonly::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
    .mobile-picker { display: none; margin-bottom: 1rem; width: 100%; }
    .toolbar { display: flex; flex-wrap: wrap; gap: .7rem; align-items: center; margin-bottom: 1rem; }
    .search { flex: 1 1 280px; position: relative; }
    .search input { width: 100%; border: 1px solid var(--line); background: var(--panel); color: var(--text); border-radius: 9px; padding: .65rem .8rem .65rem 2.2rem; }
    .search::before { content: "⌕"; position: absolute; left: .8rem; top: .56rem; color: var(--muted); font-size: 1.15rem; }
    .summary { color: var(--muted); font-size: .88rem; margin-left: auto; }
    .surface { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; box-shadow: var(--shadow); overflow: hidden; }
    .table-wrap { overflow: auto; max-height: calc(100vh - 285px); }
    table { width: 100%; border-collapse: collapse; font-size: .88rem; }
    th, td { padding: .72rem .85rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; max-width: 360px; overflow-wrap: anywhere; }
    th { position: sticky; top: 0; z-index: 1; background: var(--panel-2); color: var(--muted); font-weight: 600; white-space: nowrap; }
    tr:last-child td { border-bottom: 0; }
    tbody tr:hover { background: var(--accent-soft); }
    .null { color: var(--muted); font-style: italic; }
    .blob { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--muted); }
    .empty, .loading, .error { padding: 3rem 1.25rem; text-align: center; color: var(--muted); }
    .error { color: var(--danger); }
    .footer { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .7rem; border-top: 1px solid var(--line); padding: .75rem; }
    .pager { display: flex; gap: .45rem; align-items: center; }
    .page-label { min-width: 7rem; text-align: center; color: var(--muted); font-variant-numeric: tabular-nums; }
    details { margin-top: 1rem; background: var(--panel); border: 1px solid var(--line); border-radius: 12px; }
    summary { cursor: pointer; padding: .9rem 1rem; color: var(--muted); }
    .schema-content { border-top: 1px solid var(--line); padding: 0 1rem 1rem; overflow-x: auto; }
    .schema-content table { min-width: 620px; }
    pre { margin: 1rem 0 0; padding: .9rem; background: var(--panel-2); border-radius: 9px; overflow: auto; color: var(--muted); font-size: .8rem; }
    .type { display: inline-block; background: var(--panel-2); border-radius: 5px; padding: .12rem .35rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .75rem; }
    @media (max-width: 760px) {
      .app { display: block; }
      .sidebar { display: none; }
      .main { padding-top: 1rem; }
      .mobile-picker { display: block; }
      .table-wrap { max-height: none; }
      .topbar { align-items: center; }
      .db-path { max-width: 70vw; }
      .summary { width: 100%; margin-left: 0; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand"><div class="mark">SQ</div><div><strong>SQLite Viewer</strong><small>本機資料檢視器</small></div></div>
      <div class="sidebar-title">資料表與檢視表</div>
      <nav id="object-list" class="object-list" aria-label="資料庫物件"></nav>
    </aside>
    <main class="main">
      <header class="topbar">
        <div><h1 id="title">正在載入…</h1><div id="db-path" class="db-path"></div></div>
        <span class="readonly">唯讀模式</span>
      </header>
      <select id="mobile-picker" class="mobile-picker" aria-label="選擇資料表"></select>
      <section id="viewer" hidden>
        <div class="toolbar">
          <label class="search"><span hidden>搜尋所有欄位</span><input id="search" type="search" placeholder="搜尋所有欄位…" autocomplete="off"></label>
          <label>每頁 <select id="page-size"><option>25</option><option selected>50</option><option>100</option><option>200</option></select></label>
          <span id="summary" class="summary"></span>
        </div>
        <div class="surface">
          <div id="table-wrap" class="table-wrap"><div class="loading">正在載入資料…</div></div>
          <div class="footer">
            <span id="filter-note" class="summary"></span>
            <div class="pager">
              <button id="prev" type="button">上一頁</button>
              <span id="page-label" class="page-label"></span>
              <button id="next" type="button">下一頁</button>
            </div>
          </div>
        </div>
        <details>
          <summary>欄位結構與建表 SQL</summary>
          <div id="schema" class="schema-content"></div>
        </details>
      </section>
      <div id="status" class="surface"><div class="loading">正在讀取資料庫…</div></div>
    </main>
  </div>
  <script>
    const state = { meta: null, name: null, page: 1, pageSize: 50, search: "", request: 0 };
    const $ = (id) => document.getElementById(id);

    function formatNumber(value) {
      return value == null ? "—" : new Intl.NumberFormat("zh-TW").format(value);
    }

    async function api(path) {
      const response = await fetch(path);
      const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      return payload;
    }

    function setStatus(message, kind = "loading") {
      $("status").hidden = false;
      $("status").innerHTML = "";
      const node = document.createElement("div");
      node.className = kind;
      node.textContent = message;
      $("status").appendChild(node);
      $("viewer").hidden = true;
    }

    function renderNavigation(objects) {
      const list = $("object-list");
      const picker = $("mobile-picker");
      list.innerHTML = "";
      picker.innerHTML = "";
      for (const object of objects) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "object-button";
        button.dataset.name = object.name;
        button.setAttribute("aria-current", object.name === state.name ? "true" : "false");
        const name = document.createElement("span");
        name.className = "object-name";
        name.textContent = object.type === "view" ? `◫ ${object.name}` : object.name;
        const count = document.createElement("span");
        count.className = "object-count";
        count.textContent = formatNumber(object.row_count);
        button.append(name, count);
        button.addEventListener("click", () => selectObject(object.name));
        list.appendChild(button);

        const option = document.createElement("option");
        option.value = object.name;
        option.textContent = `${object.name} (${formatNumber(object.row_count)})`;
        option.selected = object.name === state.name;
        picker.appendChild(option);
      }
    }

    function renderCell(cell) {
      const td = document.createElement("td");
      if (cell === null) {
        const span = document.createElement("span");
        span.className = "null";
        span.textContent = "NULL";
        td.appendChild(span);
      } else if (typeof cell === "object" && cell.blob_bytes !== undefined) {
        const span = document.createElement("span");
        span.className = "blob";
        span.textContent = `<BLOB ${formatNumber(cell.blob_bytes)} bytes> ${cell.preview}`;
        td.appendChild(span);
      } else {
        td.textContent = String(cell);
      }
      return td;
    }

    function renderTable(data) {
      const wrap = $("table-wrap");
      wrap.innerHTML = "";
      if (!data.columns.length) {
        wrap.innerHTML = '<div class="empty">這個物件沒有可顯示的欄位。</div>';
        return;
      }
      if (!data.rows.length) {
        wrap.innerHTML = '<div class="empty">沒有符合條件的資料。</div>';
        return;
      }
      const table = document.createElement("table");
      const thead = document.createElement("thead");
      const header = document.createElement("tr");
      for (const column of data.columns) {
        const th = document.createElement("th");
        th.scope = "col";
        th.textContent = column;
        header.appendChild(th);
      }
      thead.appendChild(header);
      const tbody = document.createElement("tbody");
      for (const row of data.rows) {
        const tr = document.createElement("tr");
        row.forEach((cell) => tr.appendChild(renderCell(cell)));
        tbody.appendChild(tr);
      }
      table.append(thead, tbody);
      wrap.appendChild(table);
    }

    function renderSchema(data) {
      const root = $("schema");
      root.innerHTML = "";
      const table = document.createElement("table");
      const headings = ["欄位", "型別", "不可為空", "預設值", "主鍵"];
      const thead = document.createElement("thead");
      const tr = document.createElement("tr");
      headings.forEach((heading) => { const th = document.createElement("th"); th.textContent = heading; tr.appendChild(th); });
      thead.appendChild(tr);
      const tbody = document.createElement("tbody");
      data.schema.forEach((column) => {
        const row = document.createElement("tr");
        const values = [column.name, column.type || "—", column.not_null ? "是" : "否", column.default ?? "—", column.primary_key ? `第 ${column.primary_key} 欄` : "—"];
        values.forEach((value, index) => {
          const cell = document.createElement("td");
          if (index === 1) { const type = document.createElement("span"); type.className = "type"; type.textContent = value; cell.appendChild(type); }
          else cell.textContent = value;
          row.appendChild(cell);
        });
        tbody.appendChild(row);
      });
      table.append(thead, tbody);
      root.appendChild(table);
      if (data.sql) { const pre = document.createElement("pre"); const code = document.createElement("code"); code.textContent = data.sql; pre.appendChild(code); root.appendChild(pre); }
    }

    async function loadPage() {
      if (!state.name) return;
      const request = ++state.request;
      $("table-wrap").innerHTML = '<div class="loading">正在載入資料…</div>';
      const params = new URLSearchParams({ name: state.name, page: state.page, page_size: state.pageSize, q: state.search });
      try {
        const data = await api(`/api/table?${params}`);
        if (request !== state.request) return;
        state.page = data.page;
        renderTable(data);
        renderSchema(data);
        $("title").textContent = data.name;
        $("summary").textContent = `${formatNumber(data.filtered_count)} 筆資料`;
        $("filter-note").textContent = data.search ? `搜尋：「${data.search}」` : `${data.type === "view" ? "檢視表" : "資料表"} · ${data.columns.length} 欄`;
        $("page-label").textContent = `第 ${formatNumber(data.page)} / ${formatNumber(data.total_pages)} 頁`;
        $("prev").disabled = data.page <= 1;
        $("next").disabled = data.page >= data.total_pages;
      } catch (error) {
        if (request === state.request) $("table-wrap").innerHTML = `<div class="error"></div>`, $("table-wrap").firstChild.textContent = error.message;
      }
    }

    function selectObject(name) {
      if (!name) return;
      state.name = name;
      state.page = 1;
      state.search = "";
      $("search").value = "";
      history.replaceState(null, "", `#${encodeURIComponent(name)}`);
      renderNavigation(state.meta.objects);
      $("mobile-picker").value = name;
      loadPage();
    }

    async function init() {
      try {
        const meta = await api("/api/meta");
        state.meta = meta;
        $("db-path").textContent = meta.path;
        document.title = `${meta.filename} · SQLite Viewer`;
        if (!meta.objects.length) {
          setStatus("資料庫裡還沒有資料表或檢視表。", "empty");
          $("title").textContent = meta.filename;
          return;
        }
        const requested = decodeURIComponent(location.hash.slice(1));
        state.name = meta.objects.some((item) => item.name === requested) ? requested : meta.objects[0].name;
        renderNavigation(meta.objects);
        $("status").hidden = true;
        $("viewer").hidden = false;
        $("mobile-picker").value = state.name;
        await loadPage();
      } catch (error) {
        $("title").textContent = "無法開啟資料庫";
        setStatus(error.message, "error");
      }
    }

    let searchTimer;
    $("search").addEventListener("input", (event) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => { state.search = event.target.value; state.page = 1; loadPage(); }, 300);
    });
    $("page-size").addEventListener("change", (event) => { state.pageSize = Number(event.target.value); state.page = 1; loadPage(); });
    $("mobile-picker").addEventListener("change", (event) => selectObject(event.target.value));
    $("prev").addEventListener("click", () => { if (state.page > 1) { state.page -= 1; loadPage(); } });
    $("next").addEventListener("click", () => { state.page += 1; loadPage(); });
    init();
  </script>
</body>
</html>
"""


class SQLiteViewerHandler(BaseHTTPRequestHandler):
    server_version = "SQLiteViewer/1.0"

    @property
    def database_path(self) -> Path:
        return self.server.database_path  # type: ignore[attr-defined]

    def send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_bytes(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(200, APP_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/favicon.ico":
            self.send_bytes(204, b"", "image/x-icon")
            return

        try:
            if parsed.path == "/api/meta":
                with closing(open_readonly(self.database_path)) as connection:
                    objects = list_objects(connection)
                self.send_json(
                    200,
                    {
                        "filename": self.database_path.name,
                        "path": str(self.database_path),
                        "readonly": True,
                        "objects": objects,
                    },
                )
                return
            if parsed.path == "/api/table":
                query = parse_qs(parsed.query)
                name = query.get("name", [""])[0]
                if not name:
                    raise ViewerError("缺少資料表名稱。")
                page = parse_integer(query.get("page", ["1"])[0], "頁碼")
                page_size = parse_integer(
                    query.get("page_size", [str(DEFAULT_PAGE_SIZE)])[0], "每頁筆數"
                )
                search = query.get("q", [""])[0]
                with closing(open_readonly(self.database_path)) as connection:
                    payload = query_object(connection, name, page, page_size, search)
                self.send_json(200, payload)
                return
            self.send_json(404, {"error": "找不到這個頁面。"})
        except ViewerError as error:
            self.send_json(400, {"error": str(error)})
        except sqlite3.Error as error:
            self.send_json(400, {"error": f"SQLite 無法完成查詢：{error}"})
        except Exception:
            self.send_json(500, {"error": "伺服器發生未預期的錯誤。請查看終端機輸出。"})
            raise

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self.send_json(405, {"error": "唯讀模式不接受寫入操作。"})

    def log_message(self, format_string: str, *args: Any) -> None:
        return


class SQLiteViewerServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: Tuple[str, int], database_path: Path):
        self.database_path = database_path
        super().__init__(address, SQLiteViewerHandler)


def parse_integer(value: str, label: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ViewerError(f"{label}必須是整數。") from error


def create_server(database_path: Path, host: str, port: int) -> SQLiteViewerServer:
    return SQLiteViewerServer((host, port), validate_database(database_path))


def port_number(value: str) -> int:
    port = parse_integer(value, "連接埠")
    if not 0 <= port <= 65_535:
        raise argparse.ArgumentTypeError("連接埠必須介於 0 和 65535。")
    return port


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="用瀏覽器開啟 SQLite 視覺化資料表（唯讀、本機、零額外套件）。"
    )
    parser.add_argument("database", nargs="?", type=Path, help="SQLite .db/.sqlite/.sqlite3 路徑")
    parser.add_argument("--host", default="127.0.0.1", help="監聽位址（預設：127.0.0.1）")
    parser.add_argument("--port", type=port_number, default=0, help="連接埠；0 代表自動選擇（預設：0）")
    parser.add_argument("--no-browser", action="store_true", help="不要自動開啟瀏覽器")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        database_path = (
            validate_database(arguments.database)
            if arguments.database is not None
            else choose_database(Path.cwd())
        )
        server = create_server(database_path, arguments.host, arguments.port)
    except (ViewerError, OSError) as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 2

    actual_port = int(server.server_address[1])
    browser_host = "127.0.0.1" if arguments.host in {"0.0.0.0", "::"} else arguments.host
    url = f"http://{browser_host}:{actual_port}/"
    print("SQLite Viewer 已啟動（唯讀模式）")
    print(f"資料庫：{database_path}")
    print(f"網址：  {url}")
    print("按 Ctrl+C 關閉")

    if not arguments.no_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSQLite Viewer 已關閉。")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
