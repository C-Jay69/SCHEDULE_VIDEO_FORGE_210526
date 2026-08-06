"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useAuth } from "@/hooks/useAuth"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Plus, Video, Calendar, Zap } from "lucide-react"

interface DashboardStats {
  videos_generated: number
  videos_limit: number
  scheduled_posts: number
  plan_name: string
  plan_status: string
  recent_projects: Array<{
    id: string
    title: string
    status: string
    created_at: string
    video_count: number
  }>
}

const planColors: Record<string, string> = {
  starter: "bg-gray-100 text-gray-700",
  creator: "bg-blue-100 text-blue-700",
  pro: "bg-violet-100 text-violet-700",
  agency: "bg-purple-100 text-purple-700",
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<DashboardStats>("/users/me/stats")
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const isUnlimited = (stats?.videos_limit ?? 0) < 0
  const usagePct = stats && !isUnlimited ? Math.min((stats.videos_generated / (stats.videos_limit || 1)) * 100, 100) : 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
          </h1>
          <p className="text-gray-500 text-sm mt-1">Here&apos;s what&apos;s happening with your content.</p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Link>
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Plan */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Zap className="w-4 h-4" /> Current Plan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold capitalize">{stats?.plan_name || "Starter"}</span>
              <Badge className={planColors[stats?.plan_name || "starter"]}>
                {stats?.plan_status || "active"}
              </Badge>
            </div>
            <Link href="/settings" className="text-xs text-violet-600 hover:underline mt-1 block">
              Manage subscription →
            </Link>
          </CardContent>
        </Card>

        {/* Videos this month */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Video className="w-4 h-4" /> Videos Generated
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {stats?.videos_generated ?? 0}
              {isUnlimited ? (
                <span className="text-sm text-gray-400 font-normal"> / Unlimited</span>
              ) : stats?.videos_limit ? (
                <span className="text-sm text-gray-400 font-normal"> / {stats.videos_limit}</span>
              ) : null}
            </div>
            {!isUnlimited && stats?.videos_limit && (
              <Progress value={usagePct} className="mt-2 h-1.5" />
            )}
          </CardContent>
        </Card>

        {/* Scheduled */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
              <Calendar className="w-4 h-4" /> Scheduled Posts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{stats?.scheduled_posts ?? 0}</div>
            <Link href="/schedule" className="text-xs text-violet-600 hover:underline mt-1 block">
              View schedule →
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Projects</h2>
        {stats?.recent_projects?.length ? (
          <div className="space-y-3">
            {stats.recent_projects.map((p) => (
              <Card key={p.id} className="hover:shadow-md transition-shadow">
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-medium text-gray-800">{p.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {p.video_count} video{p.video_count !== 1 ? "s" : ""} ·{" "}
                      {new Date(p.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge className={statusColors[p.status] || "bg-gray-100 text-gray-600"}>
                      {p.status}
                    </Badge>
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/videos`}>View</Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Video className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-gray-500 font-medium">No projects yet</p>
              <p className="text-gray-400 text-sm mt-1">Create your first project to get started</p>
              <Button asChild className="mt-4">
                <Link href="/projects/new">
                  <Plus className="w-4 h-4 mr-2" />
                  New Project
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
