import { useState, type ReactNode } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  FileText,
  Database,
  Search,
  MessageSquare,
  BarChart3,
  FolderOpen,
  PanelLeft,
} from 'lucide-react'
import { useKnowledge } from '../context/KnowledgeContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/knowledge', label: 'Knowledge', icon: Database },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
]

export default function Layout() {
  const location = useLocation()
  const { documents } = useKnowledge()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen bg-[#f3efe8] px-3 py-3 text-[#171513] md:px-5 md:py-5">
      <div className="mx-auto max-w-[1600px]">
        <div className="flex min-h-[calc(100vh-1.5rem)] overflow-hidden rounded-[28px] border border-[#d6cfc3] bg-[#f7f4ef] shadow-[0_28px_70px_rgba(21,17,12,0.08)]">
          {isSidebarOpen ? (
            <aside className="w-[260px] border-r border-[#e0d9d0] bg-[#f0ece5] md:flex md:flex-col">
              <div className="flex items-center gap-3 border-b border-[#e0d9d0] px-6 py-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[#1f1b18] bg-[#1f1b18] text-sm font-medium text-[#f6f1e8]">
                  KA
                </div>
                <div>
                  <p className="editorial-display text-lg leading-none">Knowledge Atlas</p>
                  <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-[#72685c]">Research OS</p>
                </div>
              </div>

              <nav className="flex-1 space-y-2 px-3 py-5">
                {navItems.map(({ to, label, icon: Icon }) => {
                  const active = location.pathname === to
                  return <NavLink key={to} to={to} active={active} icon={<Icon className="h-4 w-4" />} label={label} />
                })}
              </nav>

              <div className="border-t border-[#e0d9d0] p-4">
                <div className="rounded-2xl border border-[#d7d0c6] bg-[#f9f6f1] p-3">
                  <div className="mb-2 flex items-center gap-2 text-[#5c534d]">
                    <FolderOpen className="h-4 w-4" />
                    <span className="text-[11px] uppercase tracking-[0.18em]">Corpus</span>
                  </div>
                  <div className="text-2xl font-semibold text-[#171513]">{documents.length}</div>
                  <div className="mt-1 text-xs text-[#70695f]">documents indexed</div>
                </div>
              </div>
            </aside>
          ) : null}

          <main className="flex-1 overflow-auto bg-[#f7f4ef]">
            <header className="flex items-center justify-between border-b border-[#e4ddd2] bg-[#f7f4ef]/90 px-4 py-4 backdrop-blur-sm md:px-8">
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-[#70695f]">Knowledge platform</p>
                <h1 className="editorial-display mt-1 text-2xl md:text-3xl">Multi-AI Knowledge Mining</h1>
              </div>

              <div className="flex items-center gap-4">
                <button onClick={() => setIsSidebarOpen((current) => !current)} className="inline-flex items-center gap-2 rounded-full border border-[#d3c9be] bg-white px-4 py-2 text-sm font-medium text-[#1d1a17] transition hover:border-[#b79a7f] hover:text-[#1d1a17]">
                  <PanelLeft className="h-4 w-4" />
                  {isSidebarOpen ? 'Hide panel' : 'Workspace'}
                </button>
              </div>
            </header>

            <div className="p-4 md:p-8">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}

interface NavLinkProps {
  to: string
  active: boolean
  icon: ReactNode
  label: string
}

function NavLink({ to, active, icon, label }: NavLinkProps) {
  return (
    <Link
      to={to}
      className={[
        'flex items-center gap-3 rounded-2xl border px-3 py-3 text-sm font-medium transition-colors',
        active
          ? 'border-[#d7b79c] bg-[#f8f1e9] text-[#171513] shadow-[inset_0_0_0_1px_rgba(186,143,106,0.12)]'
          : 'border-transparent text-[#514a44] hover:border-[#dbd2c7] hover:bg-[#f9f6f2] hover:text-[#1d1a17]',
      ].join(' ')}
    >
      <span className={active ? 'text-[#8a5b32]' : 'text-[#5f564f]'}>{icon}</span>
      {label}
    </Link>
  )
}
