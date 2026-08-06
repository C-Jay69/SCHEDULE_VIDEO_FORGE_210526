"use client";

import { api } from "./api";

export type User = {
  id: string;
  email: string;
  role: "admin" | "user";
  name?: string | null;
  is_active: boolean;
  stripe_customer_id?: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export async function register(email: string, password: string, name: string): Promise<AuthResponse> {
  return api.post<AuthResponse>("/auth/register", { email, password, name });
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return api.post<AuthResponse>("/auth/login", { email, password });
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

export async function getMe(): Promise<User> {
  return api.get<User>("/auth/me");
}
