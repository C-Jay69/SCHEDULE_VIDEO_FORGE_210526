"use client"

import { useEffect, useState, useCallback } from "react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, UserX, Shield, ShieldOff } from "lucide-react"

interface AdminUser {
  id: string
  email: string
  name: string
  role: "user" | "admin"
  plan: string
  is_active: boolean
  created_at: string
}

const planColors: Record<string, string> = {
  free: "bg-gray-100 text-gray-600",
  scheduler: "bg-blue-100 text-blue-700",
  committed: "bg-violet-100 text-violet-700",
  intense: "bg-purple-100 text-purple-700",
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState("all")

  const fetchUsers = useCallback(async () => {
    try {
      const data = await api.get<AdminUser[]>("/admin/users")
      setUsers(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchUsers() }, [fetchUsers])

  async function toggleActive(id: string, active: boolean) {
    if (!confirm(`${active ? "Deactivate" : "Activate"} this user?`)) return
    try {
      await api.patch(`/admin/users/${id}`, { is_active: !active })
      fetchUsers()
    } catch { alert("Failed") }
  }

  async function toggleRole(id: string, role: string) {
    const newRole = role === "admin" ? "user" : "admin"
    if (!confirm(`Change role to ${newRole}?`)) return
    try {
      await api.patch(`/admin/users/${id}`, { role: newRole })
      fetchUsers()
    } catch { alert("Failed") }
  }

  const filtered = users.filter((u) => {
    const matchSearch = u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.name || "").toLowerCase().includes(search.toLowerCase())
    const matchRole = roleFilter === "all" || u.role === roleFilter
    return matchSearch && matchRole
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <span className="text-sm text-gray-500">{users.length} total</span>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input placeholder="Search users…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={roleFilter} onValueChange={setRoleFilter}>
          <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="user">User</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600">User</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Plan</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Joined</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-gray-400">Loading…</td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-gray-400">No users found</td>
              </tr>
            ) : (
              filtered.map((u) => (
                <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-800">{u.name || "—"}</p>
                      <p className="text-xs text-gray-400">{u.email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={planColors[u.plan] || "bg-gray-100 text-gray-600"}>
                      {u.plan}
                    </Badge>
                    {u.role === "admin" && (
                      <Badge className="ml-1 bg-red-100 text-red-700">admin</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <Badge className={u.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}>
                      {u.is_active ? "active" : "inactive"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleRole(u.id, u.role)}
                        title={u.role === "admin" ? "Remove admin" : "Make admin"}
                      >
                        {u.role === "admin" ? <ShieldOff className="w-4 h-4 text-gray-400" /> : <Shield className="w-4 h-4 text-gray-400" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleActive(u.id, u.is_active)}
                        title={u.is_active ? "Deactivate" : "Activate"}
                        className={u.is_active ? "text-red-400 hover:text-red-600" : "text-green-500 hover:text-green-700"}
                      >
                        <UserX className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
