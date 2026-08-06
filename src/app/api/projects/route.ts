import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";

export async function POST(req: NextRequest) {
  try {
    const currentUser = await requireAuth();
    const { name, description, topic } = await req.json();

    if (!topic) {
      return NextResponse.json({ error: "Topic is required" }, { status: 400 });
    }

    const project = await db.project.create({
      data: {
        name: name || topic,
        description: description || null,
        topic,
        userId: currentUser.id,
      },
    });

    return NextResponse.json({ id: project.id, name: project.name });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message || "Failed to create project" }, { status });
  }
}
