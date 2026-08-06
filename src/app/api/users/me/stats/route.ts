import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { db } from "@/lib/db";

export async function GET() {
  try {
    const currentUser = await requireAuth();

    const videosGenerated = await db.video.count({
      where: { userId: currentUser.id },
    });

    const recentProjects = await db.project.findMany({
      where: { userId: currentUser.id },
      orderBy: { createdAt: "desc" },
      take: 5,
      include: { _count: { select: { videos: true } } },
    });

    return NextResponse.json({
      videos_generated: videosGenerated,
      videos_limit: currentUser.plan === "starter" ? 3 : -1,
      scheduled_posts: 0,
      plan_name: currentUser.plan,
      plan_status: "active",
      recent_projects: recentProjects.map((p) => ({
        id: p.id,
        title: p.name,
        status: "active",
        created_at: p.createdAt.toISOString(),
        video_count: p._count.videos,
      })),
    });
  } catch (err: any) {
    const status = err.status || 500;
    return NextResponse.json({ error: err.message || "Failed" }, { status });
  }
}
