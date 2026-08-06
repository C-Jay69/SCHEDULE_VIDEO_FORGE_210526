"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, apiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Eye,
  RefreshCw,
  Search,
  Video,
  PlusCircle,
  Trash2,
  Loader2,
  Play,
  Clock,
} from "lucide-react";
import { toast } from "sonner";

interface VideoItem {
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
  generating_voiceover: "Recording Voice",
  assembling: "Rendering",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

interface VideosPageProps {
  onNavigate: (page: string, params?: Record<string, string>) => void;
}

export function VideosPage({ onNavigate }: VideosPageProps) {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [refreshing, setRefreshing] = useState(false);

  const fetchVideos = useCallback(async () => {
    try {
      const data = await api.get<{ items: VideoItem[]; total: number }>("/videos");
      setVideos(data.items ?? []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  // Poll for status updates every 8s
  useEffect(() => {
    const interval = setInterval(fetchVideos, 8000);
    return () => clearInterval(interval);
  }, [fetchVideos]);

  const filtered = videos.filter((v) => {
    const matchesSearch = v.title
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || v.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this video? This cannot be undone.")) return;
    try {
      await api.delete(`/videos/${id}`);
      setVideos((prev) => prev.filter((v) => v.id !== id));
      toast.success("Video deleted");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete");
    }
  }

  function handleRefresh() {
    setRefreshing(true);
    fetchVideos();
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <h1 className="text-2xl md:text-3xl font-bold text-foreground">Videos</h1>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
        disabled={refreshing}
          >
            <RefreshCw
              className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")}
            />
            Refresh
          </Button>
          <Button
            className="bg-violet-600 hover:bg-violet-700"
            size="sm"
            onClick={() => onNavigate("generate")}
          >
            <PlusCircle className="h-4 w-4 mr-2" />
            New
          </Button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="flex gap-3"
      >
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search videos…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-background"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40 bg-background">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </motion.div>

      {/* Video list */}
      <AnimatePresence mode="popLayout">
        {filtered.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Card className="border-dashed border-border">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <div className="h-12 w-12 rounded-full bg-violet-500/10 flex items-center justify-center mb-4">
                  <Video className="h-6 w-6 text-violet-500" />
                </div>
                <p className="text-muted-foreground font-medium">No videos found</p>
                <p className="text-muted-foreground/60 text-sm mt-1">
                  {search || statusFilter !== "all"
                    ? "Try adjusting your filters"
                    : "Generate your first video to get started"}
                </p>
                {!search && statusFilter === "all" && (
                  <Button
                    className="mt-4 bg-violet-600 hover:bg-violet-700"
                    onClick={() => onNavigate("generate")}
                  >
                    <PlusCircle className="h-4 w-4 mr-2" />
                    Create Project
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <div className="space-y-3">
            {filtered.map((v, i) => (
              <motion.div
                key={v.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: i * 0.03 }}
              >
                <Card
                  className="border-border/50 hover:border-violet-500/30 transition-all duration-200 cursor-pointer group"
                  onClick={() =>
                    onNavigate("video-detail", { id: v.id })
                  }
                >
                  <CardContent className="flex items-center gap-4 py-4">
                    {/* Thumbnail / Icon */}
                    <div className="w-20 h-12 rounded-lg bg-accent shrink-0 overflow-hidden flex items-center justify-center">
                      {v.status === "completed" && v.storage_key ? (
                        <Play className="h-5 w-5 text-violet-400 group-hover:scale-110 transition-transform" />
                      ) : v.status === "failed" ? (
                        <div className="h-5 w-5 rounded-full bg-red-500/20 flex items-center justify-center">
                          <span className="text-red-400 text-xs font-bold">!</span>
                        </div>
                      ) : (
                        <Loader2 className="h-4 w-4 text-muted-foreground/40 animate-spin" />
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">
                        {v.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span className="capitalize">{v.platform}</span>
                        <span>·</span>
                        <span>{v.duration}s</span>
                        <span>·</span>
                        <Clock className="h-3 w-3" />
                        <span>
                          {new Date(v.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    {/* Status + Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge
                        variant="outline"
                        className={cn(
                          STATUS_STYLES[v.status] || STATUS_STYLES.pending
                        )}
                      >
                        {STATUS_LABELS[v.status] || v.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation();
                          onNavigate("video-detail", { id: v.id });
                        }}
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(v.id);
                        }}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
