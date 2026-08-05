"use client"

import { useEffect, useState, useCallback } from "react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, RefreshCw, RotateCcw } from "lucide-react"

interface Job {
  id: string
  video_id: string
  status: string
  created_at: string
  progress_pct?: number
  error?: string
  celery_task_id?: string
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  retrying: "bg-orange-100 text-orange-700",
}

export default function AdminJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [retrying, setRetrying] = useState<string | null>(null)

  const fetchJobs = useCallback(async () => {
    try {
      const data = await api.get<{ jobs: Job[]; total: number }>("/admin/jobs")
      setJobs(data.jobs)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 15000)
    return () => clearInterval(interval)
  }, [fetchJobs])

  async function retryJob(id: string) {
    setRetrying(id)
    try {
      await api.post(`/admin/jobs/${id}/retry`, {})
      fetchJobs()
    } catch { alert("Retry failed") }
    finally { setRetrying(null) }
  }

  const filtered = jobs.filter((j) => {
    const matchSearch = (j.video_id && j.video_id.includes(search)) || j.id.includes(search)
    const matchStatus = statusFilter === "all" || j.status === statusFilter
    return matchSearch && matchStatus
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <Button variant="outline" size="sm" onClick={fetchJobs}>
          <RefreshCw className="w-4 h-4 mr-2" />Refresh
        </Button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input placeholder="Search jobs…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600">Video</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Progress</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Created</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="py-12 text-center text-gray-400">Loading…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={5} className="py-12 text-center text-gray-400">No jobs found</td></tr>
            ) : (
              filtered.map((j) => {
                return (
                  <tr key={j.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-800 font-mono text-xs">{j.video_id}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{j.id.slice(0, 8)}…</p>
                      {j.error && (
                        <p className="text-xs text-red-500 mt-1 truncate max-w-[200px]" title={j.error}>{j.error}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={statusColors[j.status] || "bg-gray-100 text-gray-600"}>{j.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{j.progress_pct ?? 0}%</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{new Date(j.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      {j.status === "failed" && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => retryJob(j.id)}
                          disabled={retrying === j.id}
                        >
                          <RotateCcw className="w-3.5 h-3.5 mr-1" />
                          {retrying === j.id ? "…" : "Retry"}
                        </Button>
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
