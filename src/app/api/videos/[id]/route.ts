import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const currentUser = await requireAuth();
    const { id } = await params;

    const video = await db.video.findFirst({
      where: { id, userId: currentUser.id },
      include: { project: { select: { name: true } } },
    });

    if (!video) return NextResponse.json({ error: "Not found" }, { status: 404 });

    return NextResponse.json({
      id: video.id,
      title: video.title,
      status: video.status,
      platform: video.platform,
      format: video.format,
      duration: video.duration,
      created_at: video.createdAt.toISOString(),
      storage_key: video.storageKey,
      stream_url: video.storageKey ? `/api/videos/stream?id=${video.id}` : undefined,
      thumbnail_url: video.storageKey ? `/api/videos/stream?id=${video.id}&thumb=1` : undefined,
      script_text: video.scriptText,
      progress: video.progress,
      error: video.error,
    });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const currentUser = await requireAuth();
    const { id } = await params;

    const video = await db.video.findFirst({ where: { id, userId: currentUser.id } });
    if (!video) return NextResponse.json({ error: "Not found" }, { status: 404 });

    if (video.storageKey) {
      const fs = await import("fs");
      const path = await import("path");
      const filePath = path.join(process.cwd(), "uploads", "videos", video.storageKey);
      if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    }

    await db.video.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
