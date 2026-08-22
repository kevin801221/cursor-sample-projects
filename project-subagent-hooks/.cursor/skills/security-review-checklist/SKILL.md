---
name: security-review-checklist
description: 審查認證、權限、資料刪除、金流相關程式碼時使用的六大安全檢查清單。寫完或審查這類程式碼時載入。
---

# 安全審查六大檢查清單

依序檢查，每一項都要有明確結論（通過／有問題／不適用）：

## 1. 授權（Authorization）
- 呼叫者能不能影響到「不是自己」的資源？
- 只檢查「有沒有登入」是不夠的——要檢查「登入的這個人有沒有權限動這個資源」
- 典型漏洞：拿 request body 裡的 `userId` 當真，沒有跟 session 比對

## 2. 資料刪除（Deletion Integrity）
- 關聯資料有沒有漏刪？（孤兒紀錄）
- 該保留的稽核紀錄有沒有被一起刪掉？（留痕義務）

## 3. 不可逆性（Irreversibility）
- 有沒有二次確認機制？
- 有沒有復原窗口（soft delete / grace period）？

## 4. 濫用（Abuse）
- 有沒有 rate limit？
- 這個端點能不能被拿來當攻擊面（枚舉使用者、耗盡資源）？

## 5. 資訊洩漏（Information Disclosure）
- 錯誤訊息有沒有洩漏內部實作細節？
- 回應內容有沒有多給不該給的欄位？

## 6. Secrets
- 有沒有硬編碼的金鑰、token、連線字串？
- 新增的設定值有沒有走環境變數？

---

> 這個 skill 是「單一事實來源」：主 agent 審查時會自動依 description 判斷載入；
> subagent（如 security-auditor）則在 prompt 裡被明確要求讀取本檔案——
> 因為官方文件未載明 subagent 是否會自動觸發 skills，明確讀檔是最可靠的傳遞方式。
