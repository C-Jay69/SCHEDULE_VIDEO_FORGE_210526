"use client"

import { useState } from "react"
import Link from "next/link"
import { Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const plans = [
  {
    name: "Starter",
    monthlyPrice: 0,
    yearlyPrice: 0,
    description: "Try it out",
    color: "border-gray-200",
    highlight: false,
    features: [
      { text: "Creates 3 Videos / Month", included: true, bold: true },
      { text: "0 AI-Visual Credits", included: true },
      { text: "Auto-Post To Channel", included: false },
      { text: "Edit & Preview Videos", included: false },
      { text: "HD Video Resolution", included: false },
      { text: "Background Music", included: false },
      { text: "Voice Cloning", included: false },
      { text: "No Watermark", included: false },
    ],
    cta: "Get Started",
    ctaVariant: "outline" as const,
    href: "/register",
    badge: null,
  },
  {
    name: "Creator",
    monthlyPrice: 19,
    yearlyPrice: 16,
    description: "Build your audience consistently",
    color: "border-violet-400",
    highlight: false,
    features: [
      { text: "Creates 25 Videos / Month", included: true, bold: true },
      { text: "50 AI-Visual Credits", included: true },
      { text: "Auto-Post To Channel", included: true },
      { text: "Edit & Preview Videos", included: true },
      { text: "HD Video Resolution", included: true },
      { text: "Background Music", included: true },
      { text: "Voice Cloning", included: false },
      { text: "No Watermark", included: true },
    ],
    cta: "Get Creator",
    ctaVariant: "default" as const,
    href: "/register?plan=creator",
    badge: null,
  },
  {
    name: "Pro",
    monthlyPrice: 49,
    yearlyPrice: 41,
    description: "Daily presence, real growth",
    color: "border-violet-600",
    highlight: true,
    features: [
      { text: "Creates 100 Videos / Month", included: true, bold: true },
      { text: "200 AI-Visual Credits", included: true },
      { text: "Auto-Post To Channel", included: true },
      { text: "Edit & Preview Videos", included: true },
      { text: "HD Video Resolution", included: true },
      { text: "Background Music", included: true },
      { text: "Voice Cloning", included: true },
      { text: "No Watermark", included: true },
    ],
    cta: "Get Pro",
    ctaVariant: "default" as const,
    href: "/register?plan=pro",
    badge: "Most Popular",
  },
  {
    name: "Agency",
    monthlyPrice: 149,
    yearlyPrice: 124,
    description: "Scale across many channels",
    color: "border-violet-800",
    highlight: false,
    features: [
      { text: "Creates 500 Videos / Month", included: true, bold: true },
      { text: "1000 AI-Visual Credits", included: true },
      { text: "Auto-Post To Channel", included: true },
      { text: "Edit & Preview Videos", included: true },
      { text: "HD Video Resolution", included: true },
      { text: "Background Music", included: true },
      { text: "Voice Cloning", included: true },
      { text: "No Watermark", included: true },
    ],
    cta: "Get Agency",
    ctaVariant: "default" as const,
    href: "/register?plan=agency",
    badge: null,
  },
]

export default function PricingPage() {
  const [yearly, setYearly] = useState(false)

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-gray-100">
        <Link href="/" className="text-xl font-bold text-violet-700">VideoForge</Link>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Log in</Link>
          <Button asChild size="sm">
            <Link href="/register">Get Started</Link>
          </Button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Simple, Transparent Pricing</h1>
          <p className="text-gray-500 text-lg">Pick a plan. Start posting. Grow on autopilot.</p>
        </div>

        {/* Toggle */}
        <div className="flex items-center justify-center gap-3 mb-12">
          <span className={cn("text-sm font-medium", !yearly ? "text-gray-900" : "text-gray-400")}>MONTHLY</span>
          <button
            onClick={() => setYearly(!yearly)}
            className={cn(
              "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
              yearly ? "bg-violet-600" : "bg-gray-300"
            )}
          >
            <span
              className={cn(
                "inline-block h-4 w-4 rounded-full bg-white shadow transition-transform",
                yearly ? "translate-x-6" : "translate-x-1"
              )}
            />
          </button>
          <span className={cn("text-sm font-medium", yearly ? "text-gray-900" : "text-gray-400")}>YEARLY</span>
          {yearly && (
            <Badge className="bg-violet-100 text-violet-700 border-violet-200">2 MONTHS FREE!</Badge>
          )}
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={cn(
                "relative rounded-2xl border-2 p-6 flex flex-col",
                plan.color,
                plan.highlight ? "shadow-xl shadow-violet-100 scale-[1.02]" : "shadow-sm"
              )}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-violet-600 text-white px-3 py-1 text-xs">{plan.badge}</Badge>
                </div>
              )}

              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-800 uppercase tracking-wide mb-1">{plan.name}</h2>
                <p className="text-gray-400 text-sm mb-4">{plan.description}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold text-gray-900">
                    ${yearly ? plan.yearlyPrice : plan.monthlyPrice}
                  </span>
                  {plan.monthlyPrice > 0 && (
                    <span className="text-gray-400 text-sm">/month</span>
                  )}
                </div>
                {yearly && plan.monthlyPrice > 0 && (
                  <p className="text-xs text-gray-400 mt-1">Billed yearly</p>
                )}
              </div>

              <ul className="space-y-3 flex-1 mb-8">
                {plan.features.map((f) => (
                  <li key={f.text} className="flex items-center gap-2 text-sm">
                    {f.included ? (
                      <Check className="w-4 h-4 text-violet-600 shrink-0" />
                    ) : (
                      <X className="w-4 h-4 text-gray-300 shrink-0" />
                    )}
                    <span className={cn(
                      f.included ? "text-gray-700" : "text-gray-400 line-through",
                      (f as any).bold ? "font-semibold" : ""
                    )}>
                      {f.text}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                asChild
                variant={plan.ctaVariant}
                className={cn(
                  "w-full",
                  plan.highlight && plan.ctaVariant === "default"
                    ? "bg-violet-600 hover:bg-violet-700"
                    : ""
                )}
              >
                <Link href={plan.href}>{plan.cta}</Link>
              </Button>
            </div>
          ))}
        </div>

        {/* FAQ teaser */}
        <p className="text-center text-sm text-gray-400 mt-12">
          All plans include a 7-day free trial. No credit card required for Free.{" "}
          <Link href="mailto:support@videoforge.io" className="text-violet-600 hover:underline">
            Questions? Contact us.
          </Link>
        </p>
      </div>
    </div>
  )
}
