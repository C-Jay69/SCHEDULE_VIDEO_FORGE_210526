"use client"
// @ts-ignore: ignore missing @types/react in this environment
import { useEffect, useState, type FormEvent } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any
    }
  }
}

const planLabels: Record<string, { label: string; color: string }> = {
  starter: { label: "Starter — Free", color: "bg-gray-100 text-gray-700" },
  creator: { label: "Creator — $19/mo", color: "bg-blue-100 text-blue-700" },
  pro: { label: "Pro — $49/mo", color: "bg-violet-100 text-violet-700" },
  agency: { label: "Agency — $149/mo", color: "bg-purple-100 text-purple-700" },
}

type Addon = { key: string; label: string; price_cents: number }
type Grant = {
  product_key: string
  quantity: number
  created_at: string
  expires_at: string | null
}

export default function SettingsPage() {
  const { user, refetch } = useAuth()
  const [profileForm, setProfileForm] = useState({
    name: user?.name || "",
    email: user?.email || "",
  })
  const [planName, setPlanName] = useState("starter")
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
  const [addons, setAddons] = useState<Addon[]>([])
  const [grants, setGrants] = useState<Grant[]>([])
  const [buyingKey, setBuyingKey] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<Addon[]>("/billing/addons")
      .then(setAddons)
      .catch(() => setAddons([]))
    api
      .get<Grant[]>("/billing/addon-grants")
      .then(setGrants)
      .catch(() => setGrants([]))
  }, [])

  useEffect(() => {
    if (user) {
      setProfileForm({ name: user.name || "", email: user.email || "" })
    }
    api
      .get<{ plan: string }>("/users/me")
      .then((d) => d.plan && setPlanName(d.plan))
      .catch(() => {})
  }, [user])

    async function handleProfileSave(e: FormEvent) {
    e.preventDefault()
    setProfileError("")
    setProfileSuccess("")
    setProfileLoading(true)
    try {
      await api.patch("/users/me", profileForm)
      refetch?.()
      setProfileSuccess("Profile updated successfully")
    } catch (err: any) {
      setProfileError(err.message || "Failed to update profile")
    } finally {
      setProfileLoading(false)
    }
  }

  async function handlePasswordChange(e: FormEvent) {
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
      const { portal_url } = await api.get<{ portal_url: string }>("/billing/portal")
      window.location.href = portal_url
    } catch {
      alert("Failed to open billing portal")
    } finally {
      setBillingLoading(false)
    }
  }

  async function buyAddon(key: string) {
    setBuyingKey(key)
    try {
      const { checkout_url } = await api.post<{ checkout_url: string }>("/billing/checkout/addon", {
        product_key: key,
        quantity: 1,
      })
      window.location.href = checkout_url
    } catch (err: any) {
      alert(err.message || "Failed to start checkout")
    } finally {
      setBuyingKey(null)
    }
  }

  const planKey = planName || "starter"
  const plan = planLabels[planKey] || planLabels.starter

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
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-3 py-2 rounded">
                {profileSuccess}
              </div>
            )}
            {profileError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded">{profileError}</div>
            )}
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={profileForm.name}
                onChange={(e) => setProfileForm((f) => ({ ...f, name: e.target.value }))}
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
              {profileLoading ? "Saving…" : "Save Changes"}
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
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-3 py-2 rounded">
                {passwordSuccess}
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
              {passwordLoading ? "Changing…" : "Change Password"}
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
              {billingLoading ? "Opening…" : "Manage Billing"}
            </Button>
            {planKey === "starter" && (
              <Button asChild>
                <a href="/pricing">Upgrade Plan</a>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Add-ons */}
      <Card>
        <CardHeader>
          <CardTitle>Add-ons</CardTitle>
          <CardDescription>
            One-time purchases — extra AI-visual credits, voice cloning packs, and brand kit
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {addons.length === 0 ? (
            <p className="text-sm text-gray-400">
              No add-ons available yet. Configure their prices in Stripe to enable them.
            </p>
          ) : (
            addons.map((a) => {
              const owned = grants.find((g) => g.product_key === a.key)
              return (
                <div
                  key={a.key}
                  className="flex items-center justify-between gap-3 border border-gray-200 rounded-lg px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-800">{a.label}</p>
                    {owned ? (
                      <p className="text-xs text-green-600 mt-0.5">
                        Owned — {owned.quantity} {owned.quantity === 1 ? "unit" : "units"}
                        {owned.expires_at
                          ? ` · expires ${new Date(owned.expires_at).toLocaleDateString()}`
                          : ""}
                      </p>
                    ) : (
                      <p className="text-xs text-gray-400 mt-0.5">One-time payment</p>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm font-semibold text-gray-900">
                      ${(a.price_cents / 100).toFixed(0)}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => buyAddon(a.key)}
                      disabled={buyingKey !== null}
                    >
                      {buyingKey === a.key ? "Opening…" : owned ? "Buy More" : "Buy"}
                    </Button>
                  </div>
                </div>
              )
            })
          )}
        </CardContent>
      </Card>
    </div>
  )
}
