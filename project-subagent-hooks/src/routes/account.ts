import { users, auditLogs } from "../db.ts";

export interface DeleteAccountRequest {
  currentUserId: string;
  targetUserId: string;
  confirmPhrase: string;
}

export interface DeleteAccountResponse {
  success: boolean;
  message: string;
}

/**
 * 自助刪除帳號處理常式
 * DELETE /api/account
 */
export function handleDeleteAccount(req: DeleteAccountRequest): DeleteAccountResponse {
  const { currentUserId, targetUserId, confirmPhrase } = req;

  // 1. 授權檢查：呼叫者只能刪除自己的帳號
  if (currentUserId !== targetUserId) {
    throw new Error("403 Forbidden: 無權刪除其他使用者的帳號");
  }

  // 2. 二次確認字串檢查
  if (confirmPhrase !== "DELETE MY ACCOUNT") {
    throw new Error("400 Bad Request: 二次確認字串不相符");
  }

  // 3. 確認使用者存在
  if (!users.has(targetUserId)) {
    throw new Error("404 Not Found: 找不到該使用者帳號");
  }

  // 4. 刪除使用者
  users.delete(targetUserId);

  // 5. 寫入稽核紀錄（留痕不隨帳號刪除）
  auditLogs.push({
    id: `log_${Date.now()}`,
    userId: targetUserId,
    action: "ACCOUNT_SELF_DELETED",
    timestamp: new Date().toISOString(),
  });

  return {
    success: true,
    message: "帳號已成功刪除，相關稽核日誌已安全封存",
  };
}
