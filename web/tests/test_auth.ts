/**
 * Smoke tests for lib/auth.ts — exercises the request shape without
 * hitting the network. We mock the api module so the test runs offline.
 */

import { login, register, getMe, logout } from "../lib/auth";

jest.mock("../lib/api", () => ({
  api: {
    post: jest.fn().mockResolvedValue({
      access_token: "tok",
      token_type: "bearer",
      user: { id: "u1", email: "a@b.c", role: "user", is_active: true, created_at: "2026-08-03" },
    }),
    get: jest.fn().mockResolvedValue({
      id: "u1",
      email: "a@b.c",
      role: "user",
      is_active: true,
      created_at: "2026-08-03",
    }),
  },
}));

import { api } from "../lib/api";

describe("auth", () => {
  it("login posts email + password", async () => {
    await login("a@b.c", "pw");
    expect(api.post).toHaveBeenCalledWith("/auth/login", { email: "a@b.c", password: "pw" });
  });

  it("register posts email + password + name", async () => {
    await register("a@b.c", "pw", "Alice");
    expect(api.post).toHaveBeenCalledWith("/auth/register", { email: "a@b.c", password: "pw", name: "Alice" });
  });

  it("logout hits POST /auth/logout", async () => {
    await logout();
    expect(api.post).toHaveBeenCalledWith("/auth/logout");
  });

  it("getMe fetches /auth/me", async () => {
    const u = await getMe();
    expect(api.get).toHaveBeenCalledWith("/auth/me");
    expect(u.id).toBe("u1");
  });
});
