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
  user_email: string
  action: string
  resource_type: string
  resource_id?: string
  ip_address?: string
  created_at: string
  metadata?: Record<string, any>
}

const actionColors: Record<string, string> = {
  create: "bg-green-100 text-green-700",
  update: "bg-blue-100 text-blue-700",
  delete: "bg-red-100 text-red-700",
  login: "bg-gray-100 text-gray-600",
  logout: "bg-gray-100 text-gray-600",
  publish: "bg-purple-100 text-purple-700",
  stripe_event: "bg-yellow-100 text-yellow-700",
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [actionFilter, setActionFilter] = useState("all")
  const [expanded, setExpanded] = useState<string | null>(null)

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api.get<AuditLog[]>("/admin/logs")
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
      l.user_email.includes(search) ||
      l.action.includes(search) ||
      l.resource_type.includes(search) ||
      (l.resource_id || "").includes(search)
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
              <th className="text-left px-4 py-3 font-medium text-gray-600">User</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Action</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Resource</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">IP</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="py-12 text-center text-gray-400">Loading…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6} className="py-12 text-center text-gray-400">No logs found</td></tr>
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
                    <td className="px-4 py-3 text-gray-600 text-xs">{l.user_email}</td>
                    <td className="px-4 py-3">
                      <Badge className={actionColors[l.action] || "bg-gray-100 text-gray-600"}>
                        {l.action}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs">
                      {l.resource_type}
                      {l.resource_id && <span className="text-gray-400"> #{l.resource_id.slice(0, 8)}</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{l.ip_address || "—"}</td>
                    <td className="px-4 py-3 text-right text-xs text-violet-600">
                      {l.metadata ? (expanded === l.id ? "▲" : "▼") : "—"}
                    </td>
                  </tr>
                  {expanded === l.id && l.metadata && (
                    <tr key={`${l.id}-meta`} className="bg-gray-50">
                      <td colSpan={6} className="px-4 py-3">
                        <pre className="text-xs text-gray-600 overflow-auto max-h-32 bg-gray-100 p-3 rounded">
                          {JSON.stringify(l.metadata, null, 2)}
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
