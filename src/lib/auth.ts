import bcrypt from "bcryptjs";
import crypto from "crypto";
import { db } from "./db";
import { headers } from "next/headers";

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(
  password: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function generateToken(): string {
  return crypto.randomBytes(32).toString("hex");
}

export async function getCurrentUser(): Promise<{
  id: string;
  email: string;
  name: string | null;
  plan: string;
} | null> {
  const headersList = await headers();
  const auth = headersList.get("authorization");
  if (!auth?.startsWith("Bearer ")) return null;
  const token = auth.slice(7);
  const user = await db.user.findFirst({
    where: { token },
    select: { id: true, email: true, name: true, plan: true },
  });
  return user;
}

export async function requireAuth(): Promise<{
  id: string;
  email: string;
  name: string | null;
  plan: string;
}> {
  const user = await getCurrentUser();
  if (!user) {
    throw new AuthError("Unauthorized", 401);
  }
  return user;
}

export class AuthError extends Error {
  status: number;
  constructor(message: string, status: number = 400) {
    super(message);
    this.status = status;
    this.name = "AuthError";
  }
}
