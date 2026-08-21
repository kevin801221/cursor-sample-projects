import test from "node:test";
import assert from "node:assert/strict";
import { handleDeleteAccount, users, auditLogs } from "../src/index.ts";

test("DELETE /api/account 正常流程：使用者自助刪除帳號成功且留存稽核日誌", () => {
  users.set("u_test", { id: "u_test", email: "test@example.com", role: "user", createdAt: "2026-01-01" });

  const res = handleDeleteAccount({
    currentUserId: "u_test",
    targetUserId: "u_test",
    confirmPhrase: "DELETE MY ACCOUNT",
  });

  assert.equal(res.success, true);
  assert.equal(users.has("u_test"), false, "使用者應該已被自資料庫中移除");
  assert.ok(auditLogs.some(log => log.userId === "u_test"), "稽核日誌必須被保留");
});

test("DELETE /api/account 邊界防禦：越權刪除他人帳號必須拋出 403", () => {
  users.set("u_victim", { id: "u_victim", email: "victim@example.com", role: "user", createdAt: "2026-01-01" });

  assert.throws(
    () => {
      handleDeleteAccount({
        currentUserId: "u_attacker",
        targetUserId: "u_victim",
        confirmPhrase: "DELETE MY ACCOUNT",
      });
    },
    /403 Forbidden/
  );

  assert.equal(users.has("u_victim"), true, "受害者的帳號不應被刪除");
});

test("DELETE /api/account 邊界防禦：確認字串不符必須拋出 400", () => {
  users.set("u_test2", { id: "u_test2", email: "test2@example.com", role: "user", createdAt: "2026-01-01" });

  assert.throws(
    () => {
      handleDeleteAccount({
        currentUserId: "u_test2",
        targetUserId: "u_test2",
        confirmPhrase: "wrong phrase",
      });
    },
    /400 Bad Request/
  );
});
