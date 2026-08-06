import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import fs from "fs";
import path from "path";

export async function GET(req: NextRequest) {
  try {
    const currentUser = await requireAuth();
    const { searchParams } = new URL(req.url);
    const videoId = searchParams.get("id");

    if (!videoId) return NextResponse.json({ error: "ID required" }, { status: 400 });

    const video = await db.video.findFirst({ where: { id: videoId, userId: currentUser.id } });
    if (!video || !video.storageKey) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    const filePath = path.join(process.cwd(), "uploads", "videos", video.storageKey);
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    const fileBuffer = fs.readFileSync(filePath);
    const safeName = video.title.replace(/[^a-zA-Z0-9\-\s]/g, "").replace(/\s+/g, "_");

    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": "video/mp4",
        "Content-Disposition": `attachment; filename="${safeName}.mp4"`,
        "Content-Length": fileBuffer.length,
      },
    });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
