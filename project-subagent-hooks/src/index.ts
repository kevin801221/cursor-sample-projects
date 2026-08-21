import { handleDeleteAccount } from "./routes/account.ts";
import { users, auditLogs } from "./db.ts";

export { handleDeleteAccount, users, auditLogs };

console.log("Account API ready. Registered endpoints: DELETE /api/account");
