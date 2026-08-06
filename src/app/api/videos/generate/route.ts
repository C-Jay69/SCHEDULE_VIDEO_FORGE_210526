import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { generateVideo } from "@/lib/video-pipeline";

export async function POST(req: NextRequest) {
  try {
    const currentUser = await requireAuth();
    const { project_id, topic, tone, style, duration_seconds, settings } = await req.json();

    if (!topic) {
      return NextResponse.json({ error: "Topic is required" }, { status: 400 });
    }

    // Create video record
    const video = await db.video.create({
      data: {
        title: topic.length > 80 ? topic.slice(0, 77) + "..." : topic,
        status: "pending",
        format: settings?.format || "short-form",
        platform: "youtube",
        duration: duration_seconds || 60,
        userId: currentUser.id,
        projectId: project_id || null,
      },
    });

    // Run pipeline asynchronously (fire-and-forget from the request, but we await for demo)
    // In production, this would be a background job/queue
    generateVideo(
      video.id,
      currentUser.id,
      topic,
      tone || "informative",
      style || "documentary",
      duration_seconds || 60,
      settings?.format || "short-form"
    ).catch((err) => {
      console.error(`Video generation failed for ${video.id}:`, err);
    });

    return NextResponse.json({
      id: video.id,
      title: video.title,
      status: video.status,
    });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
