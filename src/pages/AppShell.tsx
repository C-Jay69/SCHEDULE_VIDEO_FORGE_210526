"use client";

import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Video,
  PlusCircle,
  Settings,
  LogOut,
  Zap,
  Menu,
  X,
} from "lucide-react";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard className="h-4 w-4" />, href: "/dashboard" },
  { id: "videos",    label: "Videos",    icon: <Video className="h-4 w-4" />,           href: "/videos" },
  { id: "generate",  label: "Generate",  icon: <PlusCircle className="h-4 w-4" />,   href: "/generate" },
  { id: "settings",  label: "Settings",  icon: <Settings className="h-4 w-4" />,     href: "/settings" },
];

interface AppShellProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  children: ReactNode;
}

export function AppShell({ currentPage, onNavigate, children }: AppShellProps) {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  function handleNav(page: string) {
    onNavigate(page);
    setMobileOpen(false);
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-64 h-screen fixed left-0 top-0 bg-card border-r border-border z-40">
        <div className="p-6 flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-violet-600 flex items-center justify-center">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold text-foreground">VideoForge</span>
        </div>
        <Separator className="opacity-50" />
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  currentPage === item.id
                    ? "bg-violet-600/15 text-violet-400"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </nav>
        </ScrollArea>
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 mb-3 px-2">
            <div className="h-8 w-8 rounded-full bg-violet-600/20 flex items-center justify-center text-violet-400 text-xs font-bold">
              {(user?.name || user?.email || "U").charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {user?.name || "User"}
              </p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-muted-foreground hover:text-destructive"
            onClick={() => {
              logout();
              onNavigate("login");
            }}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Mobile header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-card/80 backdrop-blur-md border-b border-border px-4 py-3 flex items-center justify-between">
        <button onClick={() => setMobileOpen(true)} className="text-foreground">
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-violet-600 flex items-center justify-center">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-foreground">VideoForge</span>
        </div>
        <div className="w-5" />
      </div>

      {/* Mobile menu overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <div className="fixed inset-0 z-40">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="md:hidden fixed left-0 top-0 bottom-0 w-[280px] z-50 bg-card border-r border-border flex flex-col"
            >
              <div className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-violet-600 flex items-center justify-center">
                    <Zap className="h-5 w-5 text-white" />
                  </div>
                  <span className="text-lg font-bold">VideoForge</span>
                </div>
                <button onClick={() => setMobileOpen(false)} className="text-muted-foreground">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <Separator />
              <nav className="flex-1 p-3 space-y-1">
                {NAV_ITEMS.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleNav(item.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors",
                      currentPage === item.id
                        ? "bg-violet-600/15 text-violet-400"
                        : "text-muted-foreground hover:text-foreground hover:bg-accent"
                    )}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                ))}
              </nav>
              <div className="p-4 border-t border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-muted-foreground"
                  onClick={() => {
                    logout();
                    handleNav("login");
                  }}
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign out
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main className="flex-1 md:ml-64 pt-14 md:pt-0">
        <div className="max-w-6xl mx-auto p-4 md:p-8">{children}</div>
      </main>
    </div>
  );
}
