"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import { api } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download, Eye, RefreshCw, Search, Video, Plus } from "lucide-react"

interface VideoItem {
  id: string
  title: string
  status: "pending" | "processing" | "completed" | "failed"
  platform: string
  format: string
  duration: string
  created_at: string
  download_url?: string
  thumbnail_url?: string
  published_at?: string
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
}

export default function VideosPage() {
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")

  const fetchVideos = useCallback(async () => {
    try {
      const data = await api.get<VideoItem[]>("/videos")
      setVideos(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchVideos()
    // Poll for status updates every 10s
    const interval = setInterval(fetchVideos, 10000)
    return () => clearInterval(interval)
  }, [fetchVideos])

  const filtered = videos.filter((v) => {
    const matchesSearch = v.title.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = statusFilter === "all" || v.status === statusFilter
    return matchesSearch && matchesStatus
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
        <h1 className="text-2xl font-bold text-gray-900">Videos</h1>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchVideos}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button asChild size="sm">
            <Link href="/projects/new">
              <Plus className="w-4 h-4 mr-2" />
              New
            </Link>
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search videos…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Video className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-gray-500 font-medium">No videos found</p>
            <p className="text-gray-400 text-sm mt-1">
              {search || statusFilter !== "all" ? "Try adjusting your filters" : "Create your first project to generate videos"}
            </p>
            {!search && statusFilter === "all" && (
              <Button asChild className="mt-4">
                <Link href="/projects/new">Create Project</Link>
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((v) => (
            <Card key={v.id} className="hover:shadow-md transition-shadow">
              <CardContent className="flex items-center gap-4 py-4">
                {/* Thumbnail */}
                <div className="w-20 h-12 rounded-lg bg-gray-100 shrink-0 overflow-hidden">
                  {v.thumbnail_url ? (
                    <img src={v.thumbnail_url} alt={v.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Video className="w-5 h-5 text-gray-300" />
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800 truncate">{v.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-400">{v.platform}</span>
                    <span className="text-gray-300">·</span>
                    <span className="text-xs text-gray-400">{v.duration}</span>
                    <span className="text-gray-300">·</span>
                    <span className="text-xs text-gray-400">{new Date(v.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Status + Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <Badge className={statusColors[v.status]}>{v.status}</Badge>
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/videos/${v.id}`}>
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      View
                    </Link>
                  </Button>
                  {v.status === "completed" && v.download_url && (
                    <Button asChild variant="outline" size="sm">
                      <a href={v.download_url} download>
                        <Download className="w-3.5 h-3.5 mr-1" />
                        Download
                      </a>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
