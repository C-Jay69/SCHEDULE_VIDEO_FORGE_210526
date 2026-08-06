import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { hashPassword, generateToken } from "@/lib/auth";

export async function POST(req: NextRequest) {
  try {
    const { email, password, name } = await req.json();

    if (!email || !password) {
      return NextResponse.json({ error: "Email and password are required" }, { status: 400 });
    }
    if (password.length < 6) {
      return NextResponse.json({ error: "Password must be at least 6 characters" }, { status: 400 });
    }

    const existing = await db.user.findUnique({ where: { email } });
    if (existing) {
      return NextResponse.json({ error: "An account with this email already exists" }, { status: 409 });
    }

    const hashed = await hashPassword(password);
    const token = generateToken();

    const user = await db.user.create({
      data: { email, password: hashed, name: name || null, token },
    });

    return NextResponse.json({
      token,
      user: { id: user.id, email: user.email, name: user.name, plan: user.plan, isAdmin: user.isAdmin },
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Registration failed" }, { status: 500 });
  }
}
