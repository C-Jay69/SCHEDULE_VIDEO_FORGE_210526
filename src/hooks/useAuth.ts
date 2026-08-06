"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

interface UserInfo {
  id: string;
  email: string;
  name: string | null;
  plan: string;
  isAdmin: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      const u = await api.get<UserInfo>("/auth/me");
      setUser(u);
    } catch {
      setUser(null);
      localStorage.removeItem("vf_token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const login = useCallback(
    async (credentials: { email: string; password: string }) => {
      const res = await api.post<{ token: string; user: UserInfo }>(
        "/auth/login",
        credentials
      );
      localStorage.setItem("vf_token", res.token);
      setUser(res.user);
    },
    []
  );

  const register = useCallback(
    async (data: {
      email: string;
      password: string;
      name?: string;
    }) => {
      const res = await api.post<{ token: string; user: UserInfo }>(
        "/auth/register",
        data
      );
      localStorage.setItem("vf_token", res.token);
      setUser(res.user);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem("vf_token");
    setUser(null);
  }, []);

  return { user, loading, login, register, logout, refetch };
}
