import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from tools.sqlite_viewer import (
    ViewerError,
    create_server,
    discover_databases,
    get_schema,
    list_objects,
    open_readonly,
    query_object,
)


class SQLiteViewerTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary_directory.name) / "class demo.db"
        connection = sqlite3.connect(self.database)
        connection.executescript(
            """
            CREATE TABLE "order data" (
                "order-id" INTEGER PRIMARY KEY,
                customer TEXT NOT NULL,
                note TEXT,
                payload BLOB
            );
            INSERT INTO "order data" VALUES (1, '王小明', '一般訂單', X'0102');
            INSERT INTO "order data" VALUES (2, 'Lin', '折扣 100%', NULL);
            INSERT INTO "order data" VALUES (3, 'Amy', NULL, NULL);
            CREATE VIEW order_names AS SELECT "order-id", customer FROM "order data";
            """
        )
        connection.close()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_discovers_and_lists_tables_and_views(self):
        self.assertEqual(
            discover_databases(Path(self.temporary_directory.name)),
            [self.database.resolve()],
        )
        with open_readonly(self.database) as connection:
            objects = list_objects(connection)
        self.assertEqual([item["name"] for item in objects], ["order data", "order_names"])
        self.assertEqual([item["row_count"] for item in objects], [3, 3])

    def test_schema_and_paginated_rows(self):
        with open_readonly(self.database) as connection:
            schema = get_schema(connection, "order data")
            page = query_object(connection, "order data", page=2, page_size=2)
        self.assertEqual(schema[0]["name"], "order-id")
        self.assertEqual(schema[0]["primary_key"], 1)
        self.assertEqual(page["filtered_count"], 3)
        self.assertEqual(page["total_pages"], 2)
        self.assertEqual(page["rows"][0][0], 3)

    def test_search_treats_wildcards_as_plain_text(self):
        with open_readonly(self.database) as connection:
            percent = query_object(connection, "order data", search="100%")
            underscore = query_object(connection, "order data", search="_")
        self.assertEqual(percent["filtered_count"], 1)
        self.assertEqual(underscore["filtered_count"], 0)

    def test_blob_is_json_safe(self):
        with open_readonly(self.database) as connection:
            page = query_object(connection, "order data", page_size=1)
        self.assertEqual(page["rows"][0][3], {"blob_bytes": 2, "preview": "0102"})
        json.dumps(page, allow_nan=False)

    def test_connection_is_read_only(self):
        with open_readonly(self.database) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM 'order data'")

    def test_rejects_unlisted_object(self):
        with open_readonly(self.database) as connection:
            with self.assertRaises(ViewerError):
                query_object(connection, 'order data"; DROP TABLE x; --')

    def test_http_ui_and_api(self):
        server = create_server(self.database, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urlopen(base_url + "/", timeout=3) as response:
                html = response.read().decode("utf-8")
            self.assertIn("SQLite Viewer", html)

            with urlopen(base_url + "/api/meta", timeout=3) as response:
                meta = json.load(response)
            self.assertTrue(meta["readonly"])
            self.assertEqual(meta["objects"][0]["name"], "order data")

            endpoint = "/api/table?name=" + quote("order data") + "&q=" + quote("王小明")
            with urlopen(base_url + endpoint, timeout=3) as response:
                data = json.load(response)
            self.assertEqual(data["filtered_count"], 1)

            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(base_url + "/api/table", data=b"x", method="POST"), timeout=3)
            self.assertEqual(raised.exception.code, 405)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
