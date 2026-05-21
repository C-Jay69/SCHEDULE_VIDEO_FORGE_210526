import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Zap, Video, Clock, Upload, Download, BarChart3, CheckCircle } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-purple-400" />
            <span className="text-xl font-bold">VideoForge</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-gray-300 hover:text-white">Log in</Button>
            </Link>
            <Link href="/register">
              <Button className="bg-purple-600 hover:bg-purple-700">Get Started Free</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-24 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-purple-900/40 border border-purple-700 rounded-full px-4 py-1.5 text-sm text-purple-300 mb-6">
            <Zap className="h-3.5 w-3.5" />
            Powered by open-source AI — no subscriptions to AI tools
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-tight">
            Generate & Schedule<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
              Short-Form Videos
            </span><br />
            with AI
          </h1>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Turn any topic into a complete short-form video — script, voiceover, subtitles, and all — then publish to YouTube or download for other platforms.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-lg px-8">
                Start for Free
              </Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="border-gray-600 text-gray-300 hover:text-white text-lg px-8">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-gray-900/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Everything you need to go viral</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Video, title: "AI Script Generation", desc: "Llama3-powered scripts tailored to your topic, tone, and style." },
              { icon: Zap, title: "Voiceover & Subtitles", desc: "Professional TTS voiceover with auto-generated burned-in captions." },
              { icon: Clock, title: "Schedule & Publish", desc: "Auto-publish to YouTube or download for Instagram, TikTok, and X." },
              { icon: Upload, title: "9:16 Vertical Video", desc: "Optimized for YouTube Shorts, Instagram Reels, and TikTok." },
              { icon: Download, title: "Download Anytime", desc: "Always download your videos and use them anywhere you want." },
              { icon: BarChart3, title: "Video History", desc: "Track all your projects, view generation status, and manage content." },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
                <div className="h-10 w-10 bg-purple-900/50 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="h-5 w-5 text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-gray-400 text-sm">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing teaser */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Simple, transparent pricing</h2>
          <p className="text-gray-400 mb-10">Start free, scale when you need to.</p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { name: "Free", price: "$0", features: ["3 videos/month", "Watermarked", "Download only"], highlight: false },
              { name: "Creator", price: "$19/mo", features: ["25 videos/month", "No watermark", "YouTube auto-publish", "10GB storage"], highlight: true },
              { name: "Pro", price: "$49/mo", features: ["Unlimited videos", "All features", "Priority queue", "50GB storage"], highlight: false },
            ].map(({ name, price, features, highlight }) => (
              <div key={name} className={`rounded-xl p-6 border ${highlight ? "border-purple-500 bg-purple-900/20" : "border-gray-700 bg-gray-800/30"}`}>
                <h3 className="text-xl font-bold mb-1">{name}</h3>
                <p className="text-3xl font-extrabold mb-4 text-purple-400">{price}</p>
                <ul className="space-y-2 mb-6">
                  {features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                      <CheckCircle className="h-4 w-4 text-purple-400 flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href="/register">
                  <Button className={`w-full ${highlight ? "bg-purple-600 hover:bg-purple-700" : "bg-gray-700 hover:bg-gray-600"}`}>
                    Get Started
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 px-6 text-center text-gray-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Zap className="h-4 w-4 text-purple-400" />
          <span className="text-white font-semibold">VideoForge</span>
        </div>
        <p>© {new Date().getFullYear()} VideoForge. Built with open-source AI tools.</p>
      </footer>
    </div>
  );
}
