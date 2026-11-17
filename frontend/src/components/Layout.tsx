import { Outlet, Link } from 'react-router-dom'
import { FileText, Database, Search, MessageSquare, BarChart3 } from 'lucide-react'
import type { ReactNode } from 'react'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-transparent">
      {/* Sidebar */}
      <aside className="hidden w-72 shrink-0 bg-[#17212b] px-5 py-6 text-white shadow-2xl shadow-slate-900/10 md:block">
        <div className="mb-10 border-b border-white/10 px-2 pb-7">
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#f47f68] text-lg font-bold text-[#17212b]">K</div>
            <div>
              <h1 className="font-serif text-xl font-semibold tracking-tight">Knowledge</h1>
              <p className="text-xs uppercase tracking-[0.2em] text-white/50">Mining studio</p>
            </div>
          </div>
          <p className="max-w-[14rem] text-sm leading-6 text-white/60">Turn dense documents into searchable, connected insight.</p>
        </div>

        <nav className="space-y-2 px-1">
          <NavLink to="/" icon={<BarChart3 className="h-5 w-5" />} label="Overview" />
          <NavLink to="/documents" icon={<FileText className="h-5 w-5" />} label="Documents" />
          <NavLink to="/knowledge" icon={<Database className="h-5 w-5" />} label="Knowledge graph" />
          <NavLink to="/search" icon={<Search className="h-5 w-5" />} label="Search" />
          <NavLink to="/chat" icon={<MessageSquare className="h-5 w-5" />} label="Ask documents" />
        </nav>

        <div className="absolute bottom-7 hidden w-56 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-white/50 lg:block">
          <span className="mb-2 block h-2 w-2 rounded-full bg-[#62c9b7] shadow-[0_0_12px_#62c9b7]" />
          Local workspace online
        </div>
      </aside>

      {/* Main Content */}
      <main className="min-w-0 flex-1 overflow-auto">
        <header className="border-b border-[#dfe6df] bg-[#f7f8f5]/80 px-5 py-6 backdrop-blur md:px-10">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.24em] text-[#167c78]">Workspace / 2026</p>
          <h2 className="font-serif text-3xl font-semibold tracking-tight text-[#17212b]">Multi-AI knowledge mining</h2>
          <nav className="mt-4 flex gap-2 overflow-x-auto md:hidden">
            <Link to="/" className="whitespace-nowrap rounded-full bg-[#17212b] px-3 py-2 text-xs font-semibold text-white">Overview</Link>
            <Link to="/documents" className="whitespace-nowrap rounded-full bg-white px-3 py-2 text-xs font-semibold text-[#34443d]">Documents</Link>
            <Link to="/search" className="whitespace-nowrap rounded-full bg-white px-3 py-2 text-xs font-semibold text-[#34443d]">Search</Link>
            <Link to="/chat" className="whitespace-nowrap rounded-full bg-white px-3 py-2 text-xs font-semibold text-[#34443d]">Ask</Link>
          </nav>
        </header>

        <div className="p-5 md:p-10">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

interface NavLinkProps {
  to: string
  icon: ReactNode
  label: string
}

function NavLink({ to, icon, label }: NavLinkProps) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
    >
      {icon}
      <span>{label}</span>
    </Link>
  )
}
