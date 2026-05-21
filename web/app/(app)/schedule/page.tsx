"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Calendar, Clock, Trash2, Video } from "lucide-react"

interface ScheduledPost {
  id: string
  video_id: string
  video_title: string
  platform: string
  scheduled_at: string
  status: "pending" | "published" | "failed" | "cancelled"
  thumbnail_url?: string
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  published: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-100 text-gray-500",
}

export default function SchedulePage() {
  const [posts, setPosts] = useState<ScheduledPost[]>([])
  const [loading, setLoading] = useState(true)

  async function fetchPosts() {
    try {
      const data = await api.get<ScheduledPost[]>("/schedule")
      setPosts(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPosts()
  }, [])

  async function handleCancel(id: string) {
    if (!confirm("Cancel this scheduled post?")) return
    try {
      await api.delete(`/schedule/${id}`)
      fetchPosts()
    } catch (e) {
      alert("Failed to cancel")
    }
  }

  // Group by date
  const grouped: Record<string, ScheduledPost[]> = {}
  posts.forEach((p) => {
    const date = new Date(p.scheduled_at).toLocaleDateString(undefined, {
      weekday: "long", year: "numeric", month: "long", day: "numeric",
    })
    if (!grouped[date]) grouped[date] = []
    grouped[date].push(p)
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Schedule</h1>
          <p className="text-gray-500 text-sm mt-1">Upcoming and past scheduled posts</p>
        </div>
        <Button asChild>
          <Link href="/projects/new">New Project</Link>
        </Button>
      </div>

      {Object.keys(grouped).length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Calendar className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-gray-500 font-medium">No scheduled posts</p>
            <p className="text-gray-400 text-sm mt-1">
              Generate a video and schedule it from the video detail page
            </p>
            <Button asChild className="mt-4">
              <Link href="/projects/new">Create Project</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        Object.entries(grouped).map(([date, datePosts]) => (
          <div key={date}>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{date}</h2>
            <div className="space-y-2">
              {datePosts.map((p) => (
                <Card key={p.id}>
                  <CardContent className="flex items-center gap-4 py-4">
                    {/* Thumbnail */}
                    <div className="w-16 h-10 rounded bg-gray-100 shrink-0 overflow-hidden">
                      {p.thumbnail_url ? (
                        <img src={p.thumbnail_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Video className="w-4 h-4 text-gray-300" />
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{p.video_title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <Clock className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-400">
                          {new Date(p.scheduled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                        <span className="text-gray-300">·</span>
                        <span className="text-xs text-gray-400 capitalize">{p.platform}</span>
                      </div>
                    </div>

                    {/* Status + Actions */}
                    <div className="flex items-center gap-2">
                      <Badge className={statusColors[p.status]}>{p.status}</Badge>
                      <Button asChild variant="ghost" size="sm">
                        <Link href={`/videos/${p.video_id}`}>View</Link>
                      </Button>
                      {p.status === "pending" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCancel(p.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
