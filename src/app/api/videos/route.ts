import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";

export async function GET() {
  try {
    const currentUser = await requireAuth();
    const videos = await db.video.findMany({
      where: { userId: currentUser.id },
      orderBy: { createdAt: "desc" },
      include: { project: { select: { name: true } } },
    });

    const items = videos.map((v) => ({
      id: v.id,
      title: v.title,
      status: v.status,
      platform: v.platform,
      format: v.format,
      duration: v.duration,
      created_at: v.createdAt.toISOString(),
      storage_key: v.storageKey,
      stream_url: v.storageKey ? `/api/videos/stream?id=${v.id}` : undefined,
    }));

    return NextResponse.json({ items, total: items.length });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const currentUser = await requireAuth();
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");
    if (!id) return NextResponse.json({ error: "ID required" }, { status: 400 });

    const video = await db.video.findFirst({ where: { id, userId: currentUser.id } });
    if (!video) return NextResponse.json({ error: "Not found" }, { status: 404 });

    // Delete file from disk
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
