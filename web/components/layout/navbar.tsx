"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Video, Calendar, Link2, Settings, LogOut, Zap, Menu, X
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/videos", label: "Videos", icon: Video },
  { href: "/schedule", label: "Schedule", icon: Calendar },
  { href: "/connect", label: "Connect", icon: Link2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!user) return null;

  return (
    <>
      {/* Sidebar for desktop */}
      <aside className="hidden md:flex flex-col w-64 h-screen fixed left-0 top-0 bg-gray-950 text-white border-r border-gray-800">
        <div className="p-6 border-b border-gray-800">
          <Link href="/dashboard" className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-purple-400" />
            <span className="text-xl font-bold">VideoForge</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                pathname.startsWith(href)
                  ? "bg-purple-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
          {user.role === "admin" && (
            <Link
              href="/admin"
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors mt-4",
                pathname.startsWith("/admin")
                  ? "bg-orange-600 text-white"
                  : "text-orange-400 hover:text-white hover:bg-gray-800"
              )}
            >
              <LayoutDashboard className="h-4 w-4" />
              Admin Panel
            </Link>
          )}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="mb-3 px-3">
            <p className="text-sm font-medium text-white truncate">{user.name}</p>
            <p className="text-xs text-gray-400 truncate">{user.email}</p>
          </div>
          <Button variant="ghost" className="w-full justify-start text-gray-400 hover:text-white" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-gray-950 border-b border-gray-800 px-4 py-3 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-purple-400" />
          <span className="font-bold text-white">VideoForge</span>
        </Link>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-white">
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-gray-950 text-white pt-16">
          <nav className="p-4 space-y-2">
            {navItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium",
                  pathname.startsWith(href) ? "bg-purple-600 text-white" : "text-gray-300"
                )}
              >
                <Icon className="h-5 w-5" />
                {label}
              </Link>
            ))}
            <button
              onClick={logout}
              className="flex items-center gap-3 px-4 py-3 text-sm text-gray-400 w-full"
            >
              <LogOut className="h-5 w-5" />
              Logout
            </button>
          </nav>
        </div>
      )}
    </>
  );
}
