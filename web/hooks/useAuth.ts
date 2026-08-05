"use client";

import { useState, useEffect, useCallback } from "react";
// Added 'login as apiLogin' to the imports below
import { getMe, logout as apiLogout, login as apiLogin, type User } from "@/lib/auth";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // --- ADDED THIS LOGIN FUNCTION ---
  const login = async (credentials: { email: string; password: string }) => {
    const response = await apiLogin(credentials.email, credentials.password);
    await fetchUser(); // Refresh user state after login
    return response;
  };

  const logout = async () => {
    await apiLogout().catch(() => {});
    setUser(null);
    window.location.href = "/login";
  };

  // Added 'login' to the return object below
  return { user, loading, login, logout, refetch: fetchUser };
}