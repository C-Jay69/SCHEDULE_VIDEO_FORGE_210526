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
    const isThumb = searchParams.get("thumb") === "1";

    if (!videoId) return NextResponse.json({ error: "ID required" }, { status: 400 });

    const video = await db.video.findFirst({ where: { id: videoId, userId: currentUser.id } });
    if (!video || !video.storageKey) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    const filePath = path.join(process.cwd(), "uploads", "videos", video.storageKey);
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    const stat = fs.statSync(filePath);
    const range = req.headers.get("range");

    if (isThumb) {
      // Return a very small placeholder - the video itself serves as preview
      return NextResponse.json({ message: "Use the video stream directly for preview" });
    }

    const mimeType = video.storageKey.endsWith(".mp4") ? "video/mp4" : "video/webm";

    if (range) {
      const parts = range.replace(/bytes=/, "").split("-");
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1;
      const chunkSize = end - start + 1;

      const fileBuffer = fs.createReadStream(filePath, { start, end });

      return new NextResponse(fileBuffer as any, {
        status: 206,
        headers: {
          "Content-Range": `bytes ${start}-${end}/${stat.size}`,
          "Accept-Ranges": "bytes",
          "Content-Length": chunkSize,
          "Content-Type": mimeType,
        },
      });
    }

    const fileBuffer = fs.readFileSync(filePath);
    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": mimeType,
        "Content-Length": stat.size,
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
