export interface User {
  id: string;
  email: string;
  role: string;
  createdAt: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  timestamp: string;
}

// In-memory mock database for fast demonstration
export const users: Map<string, User> = new Map([
  ["u_101", { id: "u_101", email: "alice@example.com", role: "user", createdAt: "2026-01-01" }],
  ["u_102", { id: "u_102", email: "bob@example.com", role: "user", createdAt: "2026-02-01" }],
]);

export const auditLogs: AuditLog[] = [];
