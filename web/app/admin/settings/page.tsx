"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Save, Trash2, Loader2 } from "lucide-react"

interface SystemSetting {
  id: string
  key: string
  value: string
  description?: string
  updated_at: string
}

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [newKey, setNewKey] = useState("")
  const [newValue, setNewValue] = useState("")
  const [newDesc, setNewDesc] = useState("")
  const [adding, setAdding] = useState(false)

  async function fetchSettings() {
    try {
      const data = await api.get<SystemSetting[]>("/admin/settings")
      setSettings(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchSettings() }, [])

  async function handleSave(setting: SystemSetting) {
    setSaving(setting.id)
    try {
      await api.put(`/admin/settings/${setting.key}`, {
        value: setting.value,
        description: setting.description,
      })
      fetchSettings()
    } catch { alert("Failed to save") }
    finally { setSaving(null) }
  }

  async function handleDelete(key: string) {
    if (!confirm(`Delete setting "${key}"?`)) return
    try {
      await api.delete(`/admin/settings/${key}`)
      fetchSettings()
    } catch { alert("Failed to delete") }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!newKey.trim()) return
    setAdding(true)
    try {
      await api.post("/admin/settings", { key: newKey, value: newValue, description: newDesc })
      setNewKey("")
      setNewValue("")
      setNewDesc("")
      fetchSettings()
    } catch { alert("Failed to add") }
    finally { setAdding(false) }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>

      {/* Add new */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add Setting</CardTitle>
          <CardDescription>Add a new key/value configuration entry</CardDescription>
        </CardHeader>
        <form onSubmit={handleAdd}>
          <CardContent className="grid grid-cols-3 gap-3">
            <div>
              <Input placeholder="Key (e.g. max_retries)" value={newKey} onChange={(e) => setNewKey(e.target.value)} required />
            </div>
            <div>
              <Input placeholder="Value" value={newValue} onChange={(e) => setNewValue(e.target.value)} />
            </div>
            <div>
              <Input placeholder="Description (optional)" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
            </div>
            <Button type="submit" disabled={adding} className="col-span-3 w-fit">
              {adding ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
              Add
            </Button>
          </CardContent>
        </form>
      </Card>

      {/* Existing settings */}
      <Card>
        <CardHeader><CardTitle className="text-base">Current Settings</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="w-5 h-5 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : settings.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-6">No settings configured</p>
          ) : (
            <div className="space-y-3">
              {settings.map((s) => (
                <div key={s.id} className="grid grid-cols-[1fr_1fr_auto] gap-3 items-end">
                  <div>
                    <p className="text-xs text-gray-500 mb-1 font-mono">{s.key}</p>
                    {s.description && <p className="text-xs text-gray-400">{s.description}</p>}
                  </div>
                  <Input
                    value={s.value}
                    onChange={(e) => {
                      setSettings((prev) =>
                        prev.map((x) => x.id === s.id ? { ...x, value: e.target.value } : x)
                      )
                    }}
                    className="font-mono text-sm"
                  />
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSave(s)}
                      disabled={saving === s.id}
                    >
                      {saving === s.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(s.key)}
                      className="text-red-400 hover:text-red-600"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
