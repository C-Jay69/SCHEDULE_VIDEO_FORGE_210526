import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    running: "bg-blue-100 text-blue-800",
    generating_script: "bg-blue-100 text-blue-800",
    generating_voiceover: "bg-blue-100 text-blue-800",
    generating_subtitles: "bg-blue-100 text-blue-800",
    assembling: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    published: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    cancelled: "bg-gray-100 text-gray-800",
    active: "bg-green-100 text-green-800",
    canceled: "bg-gray-100 text-gray-800",
  };
  return map[status] || "bg-gray-100 text-gray-800";
}

export function planColor(plan: string): string {
  const map: Record<string, string> = {
    free: "bg-gray-100 text-gray-700",
    creator: "bg-purple-100 text-purple-700",
    pro: "bg-yellow-100 text-yellow-700",
  };
  return map[plan] || "bg-gray-100 text-gray-700";
}
