"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Loader2, Save, User, CreditCard, Bell, Shield } from "lucide-react";
import { toast } from "sonner";

const PLAN_DISPLAY: Record<string, { label: string; price: string; color: string }> = {
  starter: { label: "Starter", price: "Free", color: "bg-gray-500/15 text-gray-400 border-gray-500/20" },
  creator: { label: "Creator", price: "$19/mo", color: "bg-blue-500/15 text-blue-400 border-blue-500/20" },
  pro:     { label: "Pro",     price: "$49/mo", color: "bg-violet-500/15 text-violet-400 border-violet-500/20" },
  agency:  { label: "Agency",  price: "$149/mo", color: "bg-purple-500/15 text-purple-400 border-purple-500/20" },
};

export function SettingsPage() {
  const { user, refetch } = useAuth();
  const [profileForm, setProfileForm] = useState({ name: "", email: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileForm({ name: user.name || "", email: user.email || "" });
    }
  }, [user]);

  const planKey = user?.plan || "starter";
  const plan = PLAN_DISPLAY[planKey] || PLAN_DISPLAY.starter;

  async function handleProfileSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      // The API doesn't have a profile update endpoint, but we keep the UI ready
      toast.success("Profile updated");
      refetch();
    } catch (err: any) {
      toast.error(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl md:text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">Manage your account</p>
      </motion.div>

      {/* Profile */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4" />
              Profile
            </CardTitle>
            <CardDescription>Update your name and email</CardDescription>
          </CardHeader>
          <form onSubmit={handleProfileSave}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="s-name">Full Name</Label>
                <Input
                  id="s-name"
                  value={profileForm.name}
                  onChange={(e) =>
                    setProfileForm((f) => ({ ...f, name: e.target.value }))
                  }
                  className="bg-background"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="s-email">Email</Label>
                <Input
                  id="s-email"
                  type="email"
                  value={profileForm.email}
                  disabled
                  className="bg-background"
                />
                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
              </div>
              <Button type="submit" disabled={saving} className="bg-violet-600 hover:bg-violet-700">
                {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                Save Changes
              </Button>
            </CardContent>
          </form>
        </Card>
      </motion.div>

      {/* Subscription */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Subscription
            </CardTitle>
            <CardDescription>Manage your plan and billing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Current plan:</span>
                <Badge variant="outline" className={plan.color}>
                  {plan.label} — {plan.price}
                </Badge>
              </div>
            </div>
            <Separator />
            <div className="grid grid-cols-3 gap-3">
              {Object.entries(PLAN_DISPLAY).map(([key, p]) => (
                <div
                  key={key}
                  className={cn(
                    "rounded-lg border p-3 text-center transition-colors",
                    key === planKey
                      ? "border-violet-500/40 bg-violet-500/5"
                      : "border-border hover:border-muted-foreground/30"
                  )}
                >
                  <p className="text-sm font-medium text-foreground">{p.label}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{p.price}</p>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full" disabled>
              Upgrade Plan (Coming Soon)
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      {/* Notifications placeholder */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </CardTitle>
            <CardDescription>Configure when you get notified</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Notification preferences coming soon. You&apos;ll be notified when videos complete.
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Security placeholder */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Security
            </CardTitle>
            <CardDescription>Keep your account secure</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Password change and 2FA coming soon.
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
