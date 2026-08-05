"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { api, apiUrl } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download, ArrowLeft, Calendar, Send, Loader2, RefreshCw } from "lucide-react"

interface VideoDetail {
  id: string
  title: string
  status: string
  platform: string
  format: string
  duration: number
  created_at: string
  storage_key?: string
  stream_url?: string
  thumbnail_url?: string
  schedule?: {
    id: string
    scheduled_at: string
    platform: string
    status: string
  }
  metadata?: Record<string, any>
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  published: "bg-emerald-100 text-emerald-700",
}

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [video, setVideo] = useState<VideoDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [scheduling, setScheduling] = useState(false)
  const [scheduleForm, setScheduleForm] = useState({
    scheduled_at: "",
    platform: "youtube",
  })
  const [scheduleError, setScheduleError] = useState("")
  const [scheduleSuccess, setScheduleSuccess] = useState("")

  async function fetchVideo() {
    try {
      const data = await api.get<VideoDetail>(`/videos/${id}`)
      setVideo(data)
    } catch {
      router.push("/videos")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVideo()
  }, [id])

  async function handleSchedule(e: React.FormEvent) {
    e.preventDefault()
    if (!scheduleForm.scheduled_at) {
      setScheduleError("Please select a date and time")
      return
    }
    setScheduleError("")
    setScheduling(true)
    try {
      await api.post(`/videos/${id}/schedule`, scheduleForm)
      setScheduleSuccess("Video scheduled successfully!")
      fetchVideo()
    } catch (err: any) {
      setScheduleError(err.message || "Failed to schedule")
    } finally {
      setScheduling(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!video) return null

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back
        </Button>
        <Badge className={statusColors[video.status]}>{video.status}</Badge>
        <Button variant="ghost" size="sm" onClick={fetchVideo}>
          <RefreshCw className="w-3.5 h-3.5" />
        </Button>
      </div>

      <h1 className="text-2xl font-bold text-gray-900">{video.title}</h1>

      {/* Video preview */}
      <Card>
        <CardContent className="p-0 overflow-hidden rounded-xl">
          {video.stream_url ? (
            <video
              src={video.stream_url}
              controls
              className="w-full aspect-video bg-black"
              poster={video.thumbnail_url}
            />
          ) : video.thumbnail_url ? (
            <img src={video.thumbnail_url} alt={video.title} className="w-full aspect-video object-cover" />
          ) : (
            <div className="w-full aspect-video bg-gray-100 flex items-center justify-center text-gray-400">
              {video.status === "processing" ? (
                <div className="flex flex-col items-center gap-2">
                  <Loader2 className="w-8 h-8 animate-spin" />
                  <span className="text-sm">Generating video…</span>
                </div>
              ) : (
                <span className="text-sm">No preview available</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Meta */}
      <Card>
        <CardHeader><CardTitle className="text-base">Details</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Platform</span><p className="font-medium capitalize mt-0.5">{video.platform}</p></div>
          <div><span className="text-gray-500">Format</span><p className="font-medium mt-0.5">{video.format}</p></div>
          <div><span className="text-gray-500">Duration</span><p className="font-medium mt-0.5">{video.duration}</p></div>
          <div><span className="text-gray-500">Created</span><p className="font-medium mt-0.5">{new Date(video.created_at).toLocaleString()}</p></div>
          {video.schedule && (
            <div><span className="text-gray-500">Scheduled</span><p className="font-medium mt-0.5">{new Date(video.schedule.scheduled_at).toLocaleString()}</p></div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      {video.status === "completed" && (
        <Button asChild variant="outline" className="w-full">
          <a href={apiUrl(`/videos/${id}/download`)} download>
            <Download className="w-4 h-4 mr-2" />
            Download Video
          </a>
        </Button>
      )}

      {/* Schedule */}
      {video.status === "completed" && !video.schedule && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Schedule Post
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSchedule} className="space-y-4">
                {scheduleError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded">
                    {scheduleError}
                  </div>
                )}
                {scheduleSuccess && (
                  <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-3 py-2 rounded">
                    {scheduleSuccess}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Date & Time</Label>
                    <Input
                      type="datetime-local"
                      value={scheduleForm.scheduled_at}
                      onChange={(e) => setScheduleForm((f) => ({ ...f, scheduled_at: e.target.value }))}
                      min={new Date().toISOString().slice(0, 16)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Platform</Label>
                    <Select
                      value={scheduleForm.platform}
                      onValueChange={(v) => setScheduleForm((f) => ({ ...f, platform: v }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="youtube">YouTube</SelectItem>
                        <SelectItem value="instagram">Instagram (metadata)</SelectItem>
                        <SelectItem value="tiktok">TikTok (metadata)</SelectItem>
                        <SelectItem value="x">X / Twitter (metadata)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button type="submit" disabled={scheduling} className="w-full">
                  {scheduling ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Scheduling…</>
                  ) : (
                    <><Send className="w-4 h-4 mr-2" />Schedule Post</>
                  )}
                </Button>
              </form>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
