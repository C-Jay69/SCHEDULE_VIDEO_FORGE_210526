"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, ExternalLink, Youtube, Instagram, Music, Twitter } from "lucide-react"

interface ConnectionStatus {
  youtube: boolean
  instagram: boolean
  tiktok: boolean
  x: boolean
}

export default function ConnectPage() {
  const [connections, setConnections] = useState<ConnectionStatus>({
    youtube: false, instagram: false, tiktok: false, x: false,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<{ platform: string; name: string; connected: boolean }[]>("/social/connections")
      .then((list) => {
        setConnections((prev) => {
          const next: ConnectionStatus = { ...prev }
          list.forEach((c) => {
            if (c.platform in next) next[c.platform as keyof ConnectionStatus] = c.connected
          })
          return next
        })
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  async function connectYouTube() {
    try {
      const { auth_url } = await api.get<{ auth_url: string }>("/social/youtube/auth")
      window.location.href = auth_url
    } catch {
      alert("Failed to start YouTube OAuth")
    }
  }

  async function disconnect(platform: string) {
    if (!confirm(`Disconnect ${platform}?`)) return
    try {
      await api.delete(`/social/${platform}`)
      setConnections((c) => ({ ...c, [platform]: false }))
    } catch {
      alert("Failed to disconnect")
    }
  }

  const platforms = [
    {
      key: "youtube",
      name: "YouTube",
      icon: <Youtube className="w-6 h-6 text-red-500" />,
      description: "Auto-publish Shorts and long-form videos directly to your channel.",
      features: ["Auto-upload", "Title & description", "Thumbnail upload", "Scheduling"],
      action: "OAuth",
      onConnect: connectYouTube,
    },
    {
      key: "instagram",
      name: "Instagram / Reels",
      icon: <Instagram className="w-6 h-6 text-pink-500" />,
      description: "Download your video + metadata package, then upload manually.",
      features: ["Video file", "Caption file", "Hashtag suggestions"],
      action: "Download Guide",
      onConnect: () => window.open("https://help.instagram.com/1315209495475854", "_blank"),
    },
    {
      key: "tiktok",
      name: "TikTok",
      icon: <Music className="w-6 h-6 text-gray-800" />,
      description: "Download your video + metadata package optimized for TikTok.",
      features: ["Video file", "Caption text", "Sound suggestions"],
      action: "Download Guide",
      onConnect: () => window.open("https://www.tiktok.com/creator-portal/", "_blank"),
    },
    {
      key: "x",
      name: "X / Twitter",
      icon: <Twitter className="w-6 h-6 text-blue-400" />,
      description: "Export video and tweet copy, post manually from X.",
      features: ["Video file", "Tweet text", "Thread format"],
      action: "Download Guide",
      onConnect: () => window.open("https://help.twitter.com/en/using-x/how-to-tweet", "_blank"),
    },
  ]

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Connect Platforms</h1>
        <p className="text-gray-500 text-sm mt-1">
          Connect YouTube for auto-publishing, or download metadata packages for other platforms.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-4">
          {platforms.map((p) => {
            const connected = connections[p.key as keyof ConnectionStatus]
            return (
              <Card key={p.key}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {p.icon}
                      <div>
                        <CardTitle className="text-base">{p.name}</CardTitle>
                        {connected && (
                          <div className="flex items-center gap-1 mt-0.5">
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="text-xs text-green-600">Connected</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {connected && p.key === "youtube" ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => disconnect(p.key)}
                          className="text-red-500 hover:text-red-700"
                        >
                          Disconnect
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant={p.action === "OAuth" ? "default" : "outline"}
                          onClick={p.onConnect}
                        >
                          {p.action === "Download Guide" && <ExternalLink className="w-3.5 h-3.5 mr-1.5" />}
                          {connected ? "Reconnect" : p.action}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-gray-500 mb-3">{p.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {p.features.map((f) => (
                      <Badge key={f} variant="outline" className="text-xs text-gray-600">{f}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
