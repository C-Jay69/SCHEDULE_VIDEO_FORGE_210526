"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Sparkles } from "lucide-react"

const tones = ["Informative", "Entertaining", "Motivational", "Conversational", "Professional", "Humorous"]
const styles = ["Talking Head", "Slideshow", "Animated", "Documentary", "Tutorial", "Story"]
const formats = ["Shorts (9:16)", "Landscape (16:9)", "Square (1:1)"]
const durations = ["30s", "60s", "3min", "5min", "10min"]

export default function NewProjectPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const [form, setForm] = useState({
    title: "",
    topic: "",
    description: "",
    tone: "Informative",
    style: "Talking Head",
    format: "Shorts (9:16)",
    duration: "60s",
    auto_publish: false,
    platform: "youtube",
  })

  function set(key: string, value: string | boolean) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.topic.trim()) {
      setError("Topic is required")
      return
    }
    setError("")
    setLoading(true)
    try {
      const project = await api.post<{ id: string }>("/projects", form)
      router.push(`/videos`)
    } catch (err: any) {
      setError(err.message || "Failed to create project")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">New Project</h1>
        <p className="text-gray-500 text-sm mt-1">
          Describe your video and VideoForge will generate it automatically.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Topic */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content</CardTitle>
            <CardDescription>What should your video be about?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Project Name</Label>
              <Input
                id="title"
                placeholder="e.g. Tech Tips Series"
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="topic">
                Topic <span className="text-red-500">*</span>
              </Label>
              <Input
                id="topic"
                placeholder="e.g. 5 ways AI is changing software development"
                value={form.topic}
                onChange={(e) => set("topic", e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Additional Context <span className="text-gray-400 text-xs">(optional)</span></Label>
              <Textarea
                id="description"
                placeholder="Any specific points to cover, audience info, or style notes…"
                rows={3}
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Video Settings</CardTitle>
            <CardDescription>Customize how your video looks and sounds</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tone</Label>
              <Select value={form.tone} onValueChange={(v) => set("tone", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {tones.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Style</Label>
              <Select value={form.style} onValueChange={(v) => set("style", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {styles.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Format</Label>
              <Select value={form.format} onValueChange={(v) => set("format", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {formats.map((f) => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Duration</Label>
              <Select value={form.duration} onValueChange={(v) => set("duration", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {durations.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Publishing */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Publishing</CardTitle>
            <CardDescription>Where should completed videos be posted?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              {["youtube", "instagram", "tiktok", "x"].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => set("platform", p)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                    form.platform === p
                      ? "bg-violet-600 text-white border-violet-600"
                      : "border-gray-200 text-gray-600 hover:border-violet-300"
                  }`}
                >
                  {p === "youtube" ? "YouTube" : p === "x" ? "X / Twitter" : p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => set("auto_publish", !form.auto_publish)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  form.auto_publish ? "bg-violet-600" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-3 w-3 rounded-full bg-white shadow transition-transform ${
                    form.auto_publish ? "translate-x-5" : "translate-x-1"
                  }`}
                />
              </button>
              <Label className="cursor-pointer" onClick={() => set("auto_publish", !form.auto_publish)}>
                Auto-publish when ready
              </Label>
              <Badge className="bg-violet-50 text-violet-700 text-xs">Scheduler plan+</Badge>
            </div>
          </CardContent>
        </Card>

        <Button type="submit" className="w-full" size="lg" disabled={loading}>
          {loading ? (
            <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating…</>
          ) : (
            <><Sparkles className="w-4 h-4 mr-2" /> Generate Video</>
          )}
        </Button>
      </form>
    </div>
  )
}
