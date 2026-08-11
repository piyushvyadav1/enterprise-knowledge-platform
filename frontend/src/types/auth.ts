export interface User {
  id: number;
  name: string;
  email: string;

  role:
    | "admin"
    | "knowledge_manager"
    | "ceo"
    | "hr"
    | "tl"
    | "employee"
    | "guest";

  department: string;

  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserRoleUpdate {
  role:
    | "admin"
    | "knowledge_manager"
    | "ceo"
    | "hr"
    | "tl"
    | "employee"
    | "guest";
}