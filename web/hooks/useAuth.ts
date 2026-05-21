"use client";

import { useState, useEffect, useCallback } from "react";
import { getMe, logout as apiLogout, type User } from "@/lib/auth";

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

  const logout = async () => {
    await apiLogout().catch(() => {});
    setUser(null);
    window.location.href = "/login";
  };

  return { user, loading, logout, refetch: fetchUser };
}
