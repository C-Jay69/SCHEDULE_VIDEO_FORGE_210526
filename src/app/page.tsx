"use client";

import { useState, useEffect, useCallback, useSyncExternalStore } from "react";
import { useAuth } from "@/hooks/useAuth";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { AppShell } from "@/pages/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { VideosPage } from "@/pages/VideosPage";
import { VideoDetailPage } from "@/pages/VideoDetailPage";
import { GeneratePage } from "@/pages/GeneratePage";
import { SettingsPage } from "@/pages/SettingsPage";
import { Loader2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

const AUTH_ROUTES = ["login", "register"];

type RouteState = {
  page: string;
  params: Record<string, string>;
};

function parseHash(): RouteState {
  if (typeof window === "undefined") return { page: "", params: {} };
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (!hash) return { page: "", params: {} };

  const segments = hash.split("/").filter(Boolean);
  const page = segments[0] || "";
  const params: Record<string, string> = {};

  if (page === "videos" && segments.length === 2) {
    return { page: "video-detail", params: { id: segments[1] } };
  }

  return { page, params };
}

// Use useSyncExternalStore for mounted state to avoid lint issues
let mountedListeners: Array<() => void> = [];
let isMounted = false;

function subscribeMounted(cb: () => void) {
  mountedListeners.push(cb);
  return () => { mountedListeners = mountedListeners.filter((l) => l !== cb); };
}
function getMountedSnapshot() {
  return isMounted;
}
function getServerMountedSnapshot() {
  return false;
}

function markMounted() {
  isMounted = true;
  mountedListeners.forEach((l) => l());
}

// Subscribe to hash changes
function subscribeHash(cb: () => void) {
  window.addEventListener("hashchange", cb);
  return () => window.removeEventListener("hashchange", cb);
}
function getHashSnapshot() {
  return window.location.hash;
}
function getServerHashSnapshot() {
  return "";
}

export default function Home() {
  const { user, loading } = useAuth();
  const mounted = useSyncExternalStore(subscribeMounted, getMountedSnapshot, getServerMountedSnapshot);
  const hash = useSyncExternalStore(subscribeHash, getHashSnapshot, getServerHashSnapshot);

  const route = parseHash();

  // Mark as mounted on first client render
  useEffect(() => {
    markMounted();
  }, []);

  // Navigation handler
  const navigate = useCallback((page: string, params?: Record<string, string>) => {
    let newHash = "#";
    if (page === "video-detail" && params?.id) {
      newHash = `#/videos/${params.id}`;
    } else if (page) {
      newHash = `#/${page}`;
    }
    window.location.hash = newHash;
  }, []);

  // Auto-redirect on auth state changes
  useEffect(() => {
    if (loading || !mounted) return;
    const current = route.page;
    if (user && AUTH_ROUTES.includes(current)) {
      window.location.hash = "#/dashboard";
    } else if (!user && current && !AUTH_ROUTES.includes(current)) {
      window.location.hash = "#/login";
    }
  }, [user, loading, mounted, hash]);

  // Initial redirect
  useEffect(() => {
    if (loading || !mounted) return;
    if (!route.page) {
      window.location.hash = user ? "#/dashboard" : "#/login";
    }
  }, [user, loading, mounted, hash]);

  // Loading splash
  if (!mounted || loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
        <p className="text-sm text-muted-foreground">Loading VideoForge…</p>
      </div>
    );
  }

  const { page, params } = route;

  // ─── Auth pages (no shell) ───────────────────────────────────
  if (page === "login") {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="login"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <LoginPage onNavigate={navigate} />
        </motion.div>
      </AnimatePresence>
    );
  }

  if (page === "register") {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="register"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <RegisterPage onNavigate={navigate} />
        </motion.div>
      </AnimatePresence>
    );
  }

  // ─── App pages (wrapped in shell) ─────────────────────────────
  let pageContent: React.ReactNode = null;
  const pageKey = `${page}-${params.id || ""}`;

  switch (page) {
    case "dashboard":
      pageContent = <DashboardPage onNavigate={navigate} />;
      break;
    case "videos":
      pageContent = <VideosPage onNavigate={navigate} />;
      break;
    case "video-detail":
      pageContent = (
        <VideoDetailPage videoId={params.id || ""} onNavigate={navigate} />
      );
      break;
    case "generate":
      pageContent = <GeneratePage onNavigate={navigate} />;
      break;
    case "settings":
      pageContent = <SettingsPage />;
      break;
    default:
      pageContent = (
        <div className="flex flex-col items-center justify-center py-32 text-center">
          <p className="text-lg text-muted-foreground">Page not found</p>
          <button
            onClick={() => navigate(user ? "dashboard" : "login")}
            className="text-sm text-violet-500 hover:underline mt-2"
          >
            Go {user ? "home" : "to login"}
          </button>
        </div>
      );
  }

  return (
    <AppShell currentPage={page} onNavigate={navigate}>
      <AnimatePresence mode="wait">
        <motion.div
          key={pageKey}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {pageContent}
        </motion.div>
      </AnimatePresence>
    </AppShell>
  );
}
