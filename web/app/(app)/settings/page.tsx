"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, ExternalLink, CheckCircle } from "lucide-react"

const planLabels: Record<string, { label: string; color: string }> = {
  free: { label: "Free", color: "bg-gray-100 text-gray-700" },
  scheduler: { label: "Scheduler — $15/mo", color: "bg-blue-100 text-blue-700" },
  committed: { label: "Committed — $30/mo", color: "bg-violet-100 text-violet-700" },
  intense: { label: "Intense — $55/mo", color: "bg-purple-100 text-purple-700" },
}

export default function SettingsPage() {
  const { user, setUser } = useAuth()
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
  })
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })
  const [profileLoading, setProfileLoading] = useState(false)
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState("")
  const [profileError, setProfileError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [billingLoading, setBillingLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setProfileForm({ full_name: user.full_name || "", email: user.email || "" })
    }
  }, [user])

  async function handleProfileSave(e: React.FormEvent) {
    e.preventDefault()
    setProfileError("")
    setProfileSuccess("")
    setProfileLoading(true)
    try {
      const updated = await api.patch("/users/me", profileForm)
      setUser?.(updated)
      setProfileSuccess("Profile updated successfully")
    } catch (err: any) {
      setProfileError(err.message || "Failed to update profile")
    } finally {
      setProfileLoading(false)
    }
  }

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault()
    setPasswordError("")
    setPasswordSuccess("")
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError("Passwords don't match")
      return
    }
    if (passwordForm.new_password.length < 8) {
      setPasswordError("Password must be at least 8 characters")
      return
    }
    setPasswordLoading(true)
    try {
      await api.post("/auth/change-password", {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      })
      setPasswordSuccess("Password changed successfully")
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" })
    } catch (err: any) {
      setPasswordError(err.message || "Failed to change password")
    } finally {
      setPasswordLoading(false)
    }
  }

  async function openBillingPortal() {
    setBillingLoading(true)
    try {
      const { url } = await api.post<{ url: string }>("/billing/portal")
      window.location.href = url
    } catch {
      alert("Failed to open billing portal")
    } finally {
      setBillingLoading(false)
    }
  }

  const planKey = user?.plan_name || "free"
  const plan = planLabels[planKey] || planLabels.free

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Update your name and email address</CardDescription>
        </CardHeader>
        <form onSubmit={handleProfileSave}>
          <CardContent className="space-y-4">
            {profileSuccess && (
              <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-sm px-3 py-2 rounded">
                <CheckCircle className="w-4 h-4" />{profileSuccess}
              </div>
            )}
            {profileError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded">{profileError}</div>
            )}
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm((f) => ({ ...f, full_name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm((f) => ({ ...f, email: e.target.value }))}
              />
            </div>
            <Button type="submit" disabled={profileLoading}>
              {profileLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving…</> : "Save Changes"}
            </Button>
          </CardContent>
        </form>
      </Card>

      {/* Password */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>Keep your account secure</CardDescription>
        </CardHeader>
        <form onSubmit={handlePasswordChange}>
          <CardContent className="space-y-4">
            {passwordSuccess && (
              <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 text-sm px-3 py-2 rounded">
                <CheckCircle className="w-4 h-4" />{passwordSuccess}
              </div>
            )}
            {passwordError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded">{passwordError}</div>
            )}
            <div className="space-y-2">
              <Label>Current Password</Label>
              <Input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm((f) => ({ ...f, current_password: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>New Password</Label>
              <Input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm((f) => ({ ...f, new_password: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Confirm New Password</Label>
              <Input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm((f) => ({ ...f, confirm_password: e.target.value }))}
              />
            </div>
            <Button type="submit" disabled={passwordLoading}>
              {passwordLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Changing…</> : "Change Password"}
            </Button>
          </CardContent>
        </form>
      </Card>

      {/* Billing */}
      <Card>
        <CardHeader>
          <CardTitle>Subscription</CardTitle>
          <CardDescription>Manage your plan and billing</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">Current plan:</span>
            <Badge className={plan.color}>{plan.label}</Badge>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={openBillingPortal} disabled={billingLoading}>
              {billingLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ExternalLink className="w-4 h-4 mr-2" />}
              Manage Billing
            </Button>
            {planKey === "free" && (
              <Button asChild>
                <a href="/pricing">Upgrade Plan</a>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
