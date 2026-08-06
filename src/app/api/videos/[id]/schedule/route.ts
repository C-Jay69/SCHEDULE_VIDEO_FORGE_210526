import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const currentUser = await requireAuth();
    const { id } = await params;
    const { scheduled_at, platform } = await req.json();

    if (!scheduled_at) {
      return NextResponse.json({ error: "Date and time are required" }, { status: 400 });
    }

    const video = await db.video.findFirst({ where: { id, userId: currentUser.id } });
    if (!video) return NextResponse.json({ error: "Not found" }, { status: 404 });

    // Store schedule info in metadata
    const meta = video.metadata ? JSON.parse(video.metadata) : {};
    meta.schedule = { scheduled_at, platform: platform || "youtube", status: "scheduled" };
    await db.video.update({
      where: { id },
      data: { metadata: JSON.stringify(meta) },
    });

    return NextResponse.json({ success: true, message: "Video scheduled successfully!" });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
