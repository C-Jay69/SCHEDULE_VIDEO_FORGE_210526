import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { verifyPassword, generateToken, AuthError } from "@/lib/auth";

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();

    if (!email || !password) {
      return NextResponse.json({ error: "Email and password are required" }, { status: 400 });
    }

    const user = await db.user.findUnique({ where: { email } });
    if (!user || !(await verifyPassword(password, user.password))) {
      throw new AuthError("Invalid email or password", 401);
    }

    const token = generateToken();
    await db.user.update({ where: { id: user.id }, data: { token } });

    return NextResponse.json({
      token,
      user: { id: user.id, email: user.email, name: user.name, plan: user.plan },
    });
  } catch (err: any) {
    const status = err instanceof AuthError ? err.status : 500;
    return NextResponse.json({ error: err.message || "Login failed" }, { status });
  }
}
