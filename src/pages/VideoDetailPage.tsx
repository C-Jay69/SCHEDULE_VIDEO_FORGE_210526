"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { api, apiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import {
  ArrowLeft,
  Download,
  Calendar,
  Send,
  Loader2,
  RefreshCw,
  Trash2,
  Play,
  AlertCircle,
  FileText,
  Clock,
  Monitor,
} from "lucide-react";
import { toast } from "sonner";

interface VideoDetail {
  id: string;
  title: string;
  status: string;
  platform: string;
  format: string;
  duration: number;
  created_at: string;
  storage_key?: string;
  stream_url?: string;
  thumbnail_url?: string;
  script_text?: string;
  progress?: number;
  error?: string;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  generating_script: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  generating_voiceover: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  assembling: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  processing: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  completed: "bg-green-500/15 text-green-400 border-green-500/20",
  failed: "bg-red-500/15 text-red-400 border-red-500/20",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  generating_script: "Writing Script",
  generating_voiceover: "Recording Voiceover",
  assembling: "Rendering Video",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

const PROGRESS_MAP: Record<string, number> = {
  pending: 0,
  generating_script: 15,
  generating_voiceover: 40,
  assembling: 70,
  processing: 50,
  completed: 100,
  failed: 0,
};

const PHASE_ICONS: Record<string, string> = {
  pending: "queue",
  generating_script: "pen",
  generating_voiceover: "mic",
  assembling: "film",
  processing: "cpu",
};

interface VideoDetailPageProps {
  videoId: string;
  onNavigate: (page: string, params?: Record<string, string>) => void;
}

export function VideoDetailPage({ videoId, onNavigate }: VideoDetailPageProps) {
  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [scheduling, setScheduling] = useState(false);
  const [scheduleForm, setScheduleForm] = useState({
    scheduled_at: "",
    platform: "youtube",
  });
  const [scheduleMsg, setScheduleMsg] = useState<"" | "success" | "error">("");
  const [deleting, setDeleting] = useState(false);

  const fetchVideo = useCallback(async () => {
    try {
      const data = await api.get<VideoDetail>(`/videos/${videoId}`);
      setVideo(data);
    } catch {
      onNavigate("videos");
    } finally {
      setLoading(false);
    }
  }, [videoId, onNavigate]);

  useEffect(() => {
    fetchVideo();
  }, [fetchVideo]);

  // Auto-poll if still processing
  useEffect(() => {
    if (!video || video.status === "completed" || video.status === "failed")
      return;
    const interval = setInterval(fetchVideo, 5000);
    return () => clearInterval(interval);
  }, [video?.status, fetchVideo]);

  async function handleSchedule(e: React.FormEvent) {
    e.preventDefault();
    if (!scheduleForm.scheduled_at) {
      setScheduleMsg("error");
      return;
    }
    setScheduleMsg("");
    setScheduling(true);
    try {
      await api.post(`/videos/${videoId}/schedule`, {
        scheduled_at: new Date(scheduleForm.scheduled_at).toISOString(),
        platform: scheduleForm.platform,
      });
      setScheduleMsg("success");
      toast.success("Video scheduled successfully!");
    } catch (err: any) {
      setScheduleMsg("error");
      toast.error(err.message || "Failed to schedule");
    } finally {
      setScheduling(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this video permanently?")) return;
    setDeleting(true);
    try {
      await api.delete(`/videos/${videoId}`);
      toast.success("Video deleted");
      onNavigate("videos");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
      </div>
    );
  }

  if (!video) return null;

  const isCompleted = video.status === "completed" && video.storage_key;
  const isFailed = video.status === "failed";
  const isProcessing =
    !isCompleted && !isFailed && video.status !== "pending";
  const progressPct = video.progress ?? PROGRESS_MAP[video.status] ?? 0;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Back + status */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3"
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onNavigate("videos")}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
        </Button>
        <Badge
          variant="outline"
          className={cn(STATUS_STYLES[video.status] || STATUS_STYLES.pending)}
        >
          {STATUS_LABELS[video.status] || video.status}
        </Badge>
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchVideo}
          className="text-muted-foreground"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </motion.div>

      {/* Title */}
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.05 }}
        className="text-2xl font-bold text-foreground"
      >
        {video.title}
      </motion.h1>

      {/* Video player / Preview */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="border-border/50 overflow-hidden">
          <CardContent className="p-0">
            {isCompleted ? (
              <video
                src={apiUrl(`/videos/stream?id=${video.id}`)}
                controls
                autoPlay
                className="w-full aspect-video bg-black"
              />
            ) : isProcessing ? (
              <div className="w-full aspect-video bg-gradient-to-br from-violet-950/50 to-background flex flex-col items-center justify-center gap-4">
                <div className="relative">
                  <Loader2 className="h-12 w-12 animate-spin text-violet-500" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-violet-400">
                      {progressPct}%
                    </span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  {STATUS_LABELS[video.status]}…
                </p>
                <div className="w-48">
                  <Progress value={progressPct} className="h-1.5" />
                </div>
              </div>
            ) : isFailed ? (
              <div className="w-full aspect-video bg-destructive/5 flex flex-col items-center justify-center gap-3">
                <AlertCircle className="h-12 w-12 text-red-400" />
                <p className="text-sm font-medium text-red-400">
                  Generation Failed
                </p>
                {video.error && (
                  <p className="text-xs text-muted-foreground max-w-sm text-center px-4">
                    {video.error}
                  </p>
                )}
              </div>
            ) : (
              <div className="w-full aspect-video bg-accent/50 flex flex-col items-center justify-center gap-2">
                <Clock className="h-10 w-10 text-muted-foreground/30" />
                <span className="text-sm text-muted-foreground">
                  Waiting to start…
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Actions */}
      {isCompleted && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Button
            asChild
            variant="outline"
            className="w-full"
          >
            <a
              href={apiUrl(`/videos/download?id=${video.id}`)}
              download
            >
              <Download className="h-4 w-4 mr-2" />
              Download Video
            </a>
          </Button>
        </motion.div>
      )}

      {/* Details */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Platform</span>
              <p className="font-medium text-foreground capitalize mt-0.5">
                {video.platform}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Format</span>
              <p className="font-medium text-foreground mt-0.5">
                {video.format}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Duration</span>
              <p className="font-medium text-foreground mt-0.5">
                {video.duration}s
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Created</span>
              <p className="font-medium text-foreground mt-0.5">
                {new Date(video.created_at).toLocaleString()}
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Script (if available) */}
      {video.script_text && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Generated Script
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                {video.script_text}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Schedule */}
      {isCompleted && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Schedule Post
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSchedule} className="space-y-4">
                {scheduleMsg === "success" && (
                  <div className="bg-green-500/10 border border-green-500/20 text-green-400 text-sm px-4 py-2.5 rounded-lg">
                    Video scheduled successfully!
                  </div>
                )}
                {scheduleMsg === "error" && (
                  <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-2.5 rounded-lg">
                    Please select a date and time
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Date & Time</Label>
                    <Input
                      type="datetime-local"
                      value={scheduleForm.scheduled_at}
                      onChange={(e) =>
                        setScheduleForm((f) => ({
                          ...f,
                          scheduled_at: e.target.value,
                        }))
                      }
                      min={new Date().toISOString().slice(0, 16)}
                      className="bg-background"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Platform</Label>
                    <Select
                      value={scheduleForm.platform}
                      onValueChange={(v) =>
                        setScheduleForm((f) => ({ ...f, platform: v }))
                      }
                    >
                      <SelectTrigger className="bg-background">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="youtube">YouTube</SelectItem>
                        <SelectItem value="instagram">
                          Instagram
                        </SelectItem>
                        <SelectItem value="tiktok">TikTok</SelectItem>
                        <SelectItem value="x">X / Twitter</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={scheduling}
                  className="w-full bg-violet-600 hover:bg-violet-700"
                >
                  {scheduling ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Scheduling…
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Schedule Post
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Delete */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.35 }}
      >
        <Button
          variant="outline"
          className="w-full text-red-400 border-red-500/20 hover:text-red-300 hover:bg-red-500/10 hover:border-red-500/30"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4 mr-2" />
          )}
          Delete Video
        </Button>
      </motion.div>
    </div>
  );
}
