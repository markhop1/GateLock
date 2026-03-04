import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  ClockIcon, 
  UserPlusIcon, 
  Cog6ToothIcon 
} from '@heroicons/react/24/outline'
import {
  HomeIcon as HomeIconSolid,
  ClockIcon as ClockIconSolid,
  UserPlusIcon as UserPlusIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
} from '@heroicons/react/24/solid'

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: HomeIcon, iconSolid: HomeIconSolid, label: 'Inicio' },
    { path: '/history', icon: ClockIcon, iconSolid: ClockIconSolid, label: 'Historial' },
    { path: '/access', icon: UserPlusIcon, iconSolid: UserPlusIconSolid, label: 'Acceso' },
    { path: '/settings', icon: Cog6ToothIcon, iconSolid: Cog6ToothIconSolid, label: 'Ajustes' },
  ]

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-primary-50 to-primary-100/50 dark:from-gray-900 dark:to-primary-950/30">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:flex-col md:w-64 md:fixed md:inset-y-0 md:left-0 bg-white/90 dark:bg-gray-800/95 backdrop-blur border-r border-primary-200 dark:border-gray-700">
        <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4 mb-8">
            <h1 className="text-2xl font-bold text-primary-600 dark:text-primary-400">
              GateLock
            </h1>
          </div>
          <nav className="flex-1 px-2 space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              const Icon = isActive ? item.iconSolid : item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="mr-3 h-6 w-6" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 pb-20 md:pb-4 md:pl-64">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          {children}
        </div>
      </main>

      {/* Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white/90 dark:bg-gray-800/95 backdrop-blur border-t border-primary-200 dark:border-gray-700 md:hidden z-50">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            const Icon = isActive ? item.iconSolid : item.icon
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center flex-1 h-full ${
                  isActive
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs mt-1">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
