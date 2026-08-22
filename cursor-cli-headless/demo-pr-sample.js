// 測試 PR：使用者登入與密碼比對模組
export async function authenticateUser(req, db) {
  const { username, password } = req.body;
  
  // ⚠️ 潛在安全問題：直接字串拼接 SQL（SQL Injection 漏洞）
  const query = `SELECT * FROM accounts WHERE username = '${username}' AND password_hash = '${password}'`;
  
  const result = await db.query(query);
  return result.rows[0];
}
