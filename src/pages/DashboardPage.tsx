"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Video,
  Calendar,
  Zap,
  PlusCircle,
  ArrowRight,
  Loader2,
} from "lucide-react";

interface DashboardStats {
  videos_generated: number;
  videos_limit: number;
  scheduled_posts: number;
  plan_name: string;
  plan_status: string;
  recent_projects: Array<{
    id: string;
    title: string;
    status: string;
    created_at: string;
    video_count: number;
  }>;
}

const PLAN_COLORS: Record<string, string> = {
  starter: "bg-gray-500/15 text-gray-400 border-gray-500/20",
  creator: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  pro: "bg-violet-500/15 text-violet-400 border-violet-500/20",
  agency: "bg-purple-500/15 text-purple-400 border-purple-500/20",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-500/15 text-green-400",
  processing: "bg-blue-500/15 text-blue-400",
  completed: "bg-green-500/15 text-green-400",
  draft: "bg-yellow-500/15 text-yellow-400",
};

interface DashboardPageProps {
  onNavigate: (page: string) => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.get<DashboardStats>("/users/me/stats");
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
      </div>
    );
  }

  const isUnlimited = (stats?.videos_limit ?? 0) < 0;
  const usagePct =
    stats && !isUnlimited
      ? Math.min(
          ((stats.videos_generated / (stats.videos_limit || 1)) * 100),
          100
        )
      : 0;

  const planName = stats?.plan_name || user?.plan || "starter";
  const firstName = user?.name?.split(" ")[0];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground">
            Welcome back{firstName ? `, ${firstName}` : ""}
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Here&apos;s what&apos;s happening with your content.
          </p>
        </div>
        <Button
          className="bg-violet-600 hover:bg-violet-700"
          onClick={() => onNavigate("generate")}
        >
          <PlusCircle className="h-4 w-4 mr-2" />
          New Video
        </Button>
      </motion.div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Current Plan
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold capitalize text-foreground">
                  {planName.charAt(0).toUpperCase() + planName.slice(1)}
                </span>
                <Badge
                  variant="outline"
                  className={cn(PLAN_COLORS[planName] || PLAN_COLORS.starter)}
                >
                  {stats?.plan_status || "active"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Video className="h-4 w-4" />
                Videos Generated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-foreground">
                {stats?.videos_generated ?? 0}
                <span className="text-sm text-muted-foreground font-normal ml-1">
                  {isUnlimited
                    ? "/ Unlimited"
                    : stats?.videos_limit
                    ? `/ ${stats.videos_limit}`
                    : ""}
                </span>
              </div>
              {!isUnlimited && stats?.videos_limit && (
                <Progress value={usagePct} className="mt-2 h-1.5" />
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Scheduled Posts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-foreground">
                {stats?.scheduled_posts ?? 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recent Projects */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">Recent Projects</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onNavigate("videos")}
            className="text-muted-foreground"
          >
            View all
            <ArrowRight className="h-3.5 w-3.5 ml-1" />
          </Button>
        </div>

        {stats?.recent_projects?.length ? (
          <div className="space-y-3">
            {stats.recent_projects.map((p) => (
              <Card
                key={p.id}
                className="border-border/50 hover:border-violet-500/30 transition-colors cursor-pointer"
                onClick={() => onNavigate("videos")}
              >
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-medium text-foreground">{p.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {p.video_count} video{p.video_count !== 1 ? "s" : ""} ·{" "}
                      {new Date(p.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className={cn(
                        STATUS_COLORS[p.status] || STATUS_COLORS.active
                      )}
                    >
                      {p.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-dashed border-border">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <div className="h-12 w-12 rounded-full bg-violet-500/10 flex items-center justify-center mb-4">
                <Video className="h-6 w-6 text-violet-500" />
              </div>
              <p className="text-muted-foreground font-medium">No projects yet</p>
              <p className="text-muted-foreground/60 text-sm mt-1">
                Create your first video to get started
              </p>
              <Button
                className="mt-4 bg-violet-600 hover:bg-violet-700"
                onClick={() => onNavigate("generate")}
              >
                <PlusCircle className="h-4 w-4 mr-2" />
                New Project
              </Button>
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
