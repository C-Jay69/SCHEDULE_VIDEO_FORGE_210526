"use client"

import { useEffect, useState, useCallback } from "react"
import { api } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RefreshCw, Search } from "lucide-react"

interface AuditLog {
  id: string
  admin_id: string
  admin_email?: string
  action: string
  target?: string
  created_at: string
}

const actionColors: Record<string, string> = {
  create: "bg-green-100 text-green-700",
  update: "bg-blue-100 text-blue-700",
  delete: "bg-red-100 text-red-700",
  login: "bg-gray-100 text-gray-600",
  logout: "bg-gray-100 text-gray-600",
  publish: "bg-purple-100 text-purple-700",
  retry_job: "bg-orange-100 text-orange-700",
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [actionFilter, setActionFilter] = useState("all")
  const [expanded, setExpanded] = useState<string | null>(null)

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api.get<AuditLog[]>("/admin/logs?limit=200")
      setLogs(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  const filtered = logs.filter((l) => {
    const matchSearch =
      (l.admin_email || "").toLowerCase().includes(search.toLowerCase()) ||
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      (l.target || "").toLowerCase().includes(search.toLowerCase())
    const matchAction = actionFilter === "all" || l.action === actionFilter
    return matchSearch && matchAction
  })

  const uniqueActions = Array.from(new Set(logs.map((l) => l.action)))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <Button variant="outline" size="sm" onClick={fetchLogs}>
          <RefreshCw className="w-4 h-4 mr-2" />Refresh
        </Button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input placeholder="Search…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            {uniqueActions.map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600">Time</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Admin</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Action</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Target</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="py-12 text-center text-gray-400">Loading…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={4} className="py-12 text-center text-gray-400">No logs found</td></tr>
            ) : (
              filtered.map((l) => (
                <>
                  <tr
                    key={l.id}
                    className="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => setExpanded(expanded === l.id ? null : l.id)}
                  >
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                      {new Date(l.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs">{l.admin_email || l.admin_id?.slice(0, 8)}</td>
                    <td className="px-4 py-3">
                      <Badge className={actionColors[l.action] || "bg-gray-100 text-gray-600"}>
                        {l.action}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs max-w-[400px] truncate">
                      {l.target || "—"}
                    </td>
                  </tr>
                  {expanded === l.id && l.target && (
                    <tr key={`${l.id}-meta`} className="bg-gray-50">
                      <td colSpan={4} className="px-4 py-3">
                        <pre className="text-xs text-gray-600 overflow-auto max-h-32 bg-gray-100 p-3 rounded">
                          {l.target}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
