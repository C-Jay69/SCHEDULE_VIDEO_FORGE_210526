"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"
import { Users, Video, DollarSign, Activity } from "lucide-react"

interface AdminMetrics {
  total_users: number
  active_subscriptions: number
  videos_today: number
  mrr: number
  new_users_7d: Array<{ date: string; count: number }>
  videos_7d: Array<{ date: string; count: number }>
  plan_distribution: Array<{ plan: string; count: number }>
  job_stats: { pending: number; processing: number; completed: number; failed: number }
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<AdminMetrics>("/admin/metrics")
      .then(setMetrics)
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
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Activity className="w-4 h-4" />Active Subs</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.active_subscriptions ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><Video className="w-4 h-4" />Videos Today</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{m?.videos_today ?? 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500 flex gap-2"><DollarSign className="w-4 h-4" />MRR</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">${((m?.mrr ?? 0) / 100).toFixed(0)}</p></CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-base">New Users (7d)</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={m?.new_users_7d || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#7c3aed" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Videos Generated (7d)</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={m?.videos_7d || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Plan distribution + Job stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-base">Plan Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={m?.plan_distribution || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="plan" type="category" tick={{ fontSize: 11 }} width={70} />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
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
                  {m?.job_stats?.[key as keyof typeof m.job_stats] ?? 0}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
