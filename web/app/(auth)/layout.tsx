import Link from "next/link"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 to-white flex flex-col">
      <header className="flex items-center justify-center py-8">
        <Link href="/" className="text-2xl font-bold text-violet-700">
          VideoForge
        </Link>
      </header>
      <main className="flex-1 flex items-center justify-center px-4">
        {children}
      </main>
      <footer className="py-6 text-center text-xs text-gray-400">
        &copy; {new Date().getFullYear()} VideoForge. All rights reserved.
      </footer>
    </div>
  )
}
