"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Loader2,
  Sparkles,
  FileText,
  Mic,
  Film,
  Monitor,
  Upload,
} from "lucide-react";
import { toast } from "sonner";

const TONES = ["Informative", "Entertaining", "Motivational", "Conversational", "Professional", "Humorous"];
const STYLES = ["Talking Head", "Slideshow", "Animated", "Documentary", "Tutorial", "Story"];
const FORMATS = [
  { label: "Shorts (9:16)", value: "short-form" },
  { label: "Landscape (16:9)", value: "landscape" },
  { label: "Square (1:1)", value: "square" },
];
const DURATIONS = [
  { label: "30 seconds", value: 30 },
  { label: "60 seconds", value: 60 },
  { label: "3 minutes", value: 180 },
  { label: "5 minutes", value: 300 },
];

const STEPS = [
  { label: "Script", icon: FileText, color: "text-blue-400" },
  { label: "Voiceover", icon: Mic, color: "text-green-400" },
  { label: "Visuals", icon: Film, color: "text-purple-400" },
  { label: "Render", icon: Monitor, color: "text-orange-400" },
  { label: "Upload", icon: Upload, color: "text-pink-400" },
];

interface GeneratePageProps {
  onNavigate: (page: string, params?: Record<string, string>) => void;
}

export function GeneratePage({ onNavigate }: GeneratePageProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    topic: "",
    description: "",
    tone: "Informative",
    style: "Documentary",
    format: "short-form",
    duration: 60,
  });

  function set(key: string, value: string | number) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.topic.trim()) {
      setError("Topic is required");
      return;
    }
    setError("");
    setLoading(true);
    try {
      // 1. Create project
      const project = await api.post<{ id: string; name: string }>("/projects", {
        topic: form.topic,
        description: form.description || undefined,
      });
      // 2. Kick off video generation
      const video = await api.post<{ id: string }>("/videos/generate", {
        project_id: project.id,
        topic: form.topic,
        tone: form.tone.toLowerCase(),
        style: form.style.toLowerCase(),
        duration_seconds: form.duration,
        settings: { format: form.format },
      });
      toast.success("Video generation started!");
      onNavigate("video-detail", { id: video.id });
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl md:text-3xl font-bold text-foreground">
          Generate Video
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Describe your video and VideoForge will generate it automatically.
        </p>
      </motion.div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-violet-400" />
                Content
              </CardTitle>
              <CardDescription>
                What should your video be about?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="topic">
                  Topic <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="topic"
                  placeholder="e.g. 5 ways AI is changing software development"
                  value={form.topic}
                  onChange={(e) => set("topic", e.target.value)}
                  required
                  className="bg-background"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="desc">Additional Context</Label>
                <Textarea
                  id="desc"
                  placeholder="Any specific points, audience info, or style notes…"
                  rows={3}
                  value={form.description}
                  onChange={(e) => set("description", e.target.value)}
                  className="bg-background"
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Settings */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base">Video Settings</CardTitle>
              <CardDescription>
                Customize how your video looks and sounds
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tone</Label>
                <Select
                  value={form.tone}
                  onValueChange={(v) => set("tone", v)}
                >
                  <SelectTrigger className="bg-background">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TONES.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Style</Label>
                <Select
                  value={form.style}
                  onValueChange={(v) => set("style", v)}
                >
                  <SelectTrigger className="bg-background">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STYLES.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Format</Label>
                <Select
                  value={form.format}
                  onValueChange={(v) => set("format", v)}
                >
                  <SelectTrigger className="bg-background">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FORMATS.map((f) => (
                      <SelectItem key={f.value} value={f.value}>
                        {f.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Duration</Label>
                <Select
                  value={String(form.duration)}
                  onValueChange={(v) => set("duration", Number(v))}
                >
                  <SelectTrigger className="bg-background">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DURATIONS.map((d) => (
                      <SelectItem key={d.value} value={String(d.value)}>
                        {d.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Pipeline preview */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base">Pipeline Preview</CardTitle>
              <CardDescription>
                Your video goes through these stages automatically
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between gap-2">
                {STEPS.map((step, i) => {
                  const Icon = step.icon;
                  return (
                    <div key={step.label} className="flex flex-col items-center gap-1.5">
                      <div
                        className={cn(
                          "h-10 w-10 rounded-full bg-accent flex items-center justify-center",
                          step.color
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {step.label}
                      </span>
                      {i < STEPS.length - 1 && (
                        <div className="hidden sm:block absolute h-px w-full bg-border top-5" />
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-3 rounded-lg"
          >
            {error}
          </motion.div>
        )}

        {/* Submit */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Button
            type="submit"
            className="w-full bg-violet-600 hover:bg-violet-700"
            size="lg"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Starting Generation…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Video
              </>
            )}
          </Button>
        </motion.div>
      </form>
    </div>
  );
}
