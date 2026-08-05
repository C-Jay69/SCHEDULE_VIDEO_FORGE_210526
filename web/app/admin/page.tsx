"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"
import { Users, Video, DollarSign, Activity, Calendar, HardDrive } from "lucide-react"

interface AdminMetrics {
  total_users: number
  total_videos: number
  total_schedules: number
  total_published: number
  active_users: number
  mrr_cents: number
  storage_used_mb: number
  published_by_platform: Record<string, number>
}

interface Job {
  id: string
  status: string
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null)
  const [jobStats, setJobStats] = useState<{ pending: number; processing: number; completed: number; failed: number }>({
    pending: 0, processing: 0, completed: 0, failed: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<AdminMetrics>("/admin/metrics"),
      api.get<{ jobs: Job[]; total: number }>("/admin/jobs"),
    ])
      .then(([m, j]) => {
        setMetrics(m)
        const stats = { pending: 0, processing: 0, completed: 0, failed: 0 }
        j.jobs.forEach((job) => {
          if (job.status in stats) (stats as any)[job.status] += 1
        })
        setJobStats(stats)
      })
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

  const m = metrics
  const platformData = Object.entries(m?.published_by_platform || {}).map(([platform, count]) => ({
    platform: platform.charAt(0).toUpperCase() + platform.slice(1),
    count,
  }))

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Overview</h1>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Users className="w-4 h-4" />Total Users</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.total_users ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Activity className="w-4 h-4" />Active Users</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.active_users ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Video className="w-4 h-4" />Total Videos</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.total_videos ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><DollarSign className="w-4 h-4" />MRR</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">${((m?.mrr_cents ?? 0) / 100).toFixed(0)}</p></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Calendar className="w-4 h-4" />Schedules</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.total_schedules ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Video className="w-4 h-4" />Published</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.total_published ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><HardDrive className="w-4 h-4" />Storage Used</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{(m?.storage_used_mb ?? 0).toFixed(0)} MB</p></CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-base">Published by Platform</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={platformData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="platform" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Job Queue</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            {[
              { label: "Pending", key: "pending", color: "text-yellow-600" },
              { label: "Processing", key: "processing", color: "text-blue-600" },
              { label: "Completed", key: "completed", color: "text-green-600" },
              { label: "Failed", key: "failed", color: "text-red-600" },
            ].map(({ label, key, color }) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-500">{label}</p>
                <p className={`text-2xl font-bold mt-1 ${color}`}>
                  {jobStats[key as keyof typeof jobStats]}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
