import { useState } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  BookOpen,
  History,
  Settings,
  Menu,
  X,
  Search
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

export function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const location = useLocation()

  const navItems = [
    { path: '/research', icon: Search, label: 'Research' },
    { path: '/wiki', icon: BookOpen, label: 'Wiki' },
    { path: '/documents', icon: LayoutDashboard, label: 'Documents' },
    { path: '/history', icon: History, label: 'History' },
    { path: '/config', icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isSidebarOpen ? 240 : 80 }}
        className="bg-slate-900 border-r border-slate-800 flex-shrink-0 z-20 flex flex-col"
      >
        {/* Logo Area */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center shadow-lg shadow-primary-500/20">
              <span className="font-bold text-white text-lg">F</span>
            </div>
            <AnimatePresence>
              {isSidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="font-bold text-lg tracking-tight"
                >
                  FinAgent
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group',
                  isActive
                    ? 'bg-primary-600/10 text-primary-400'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                )}
              >
                <item.icon
                  className={clsx(
                    'w-5 h-5 flex-shrink-0 transition-colors',
                    isActive ? 'text-primary-400' : 'text-slate-500 group-hover:text-slate-300'
                  )}
                />
                <AnimatePresence>
                  {isSidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="ml-3 font-medium whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {/* Active Indicator */}
                {isActive && (
                  <div className="absolute left-0 w-1 h-8 bg-primary-500 rounded-r-full" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer Toggle */}
        <div className="p-4 border-t border-slate-800">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-slate-800 text-slate-500 transition-colors"
          >
            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-950 relative">
        {/* Background Glow Effects */}
        <div className="absolute top-0 left-0 w-full h-96 bg-primary-900/10 blur-[100px] pointer-events-none" />

        <div className="flex-1 overflow-y-auto relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  )
}
