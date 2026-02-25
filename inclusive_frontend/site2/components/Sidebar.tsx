'use client'

import { useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import {
  Briefcase,
  FileText,
  Map,
  MessageCircle,
  Heart,
  User,
  LogOut,
  Video,
  Menu,
  X,
} from 'lucide-react'
import { motion } from 'framer-motion'

import { MessageSquare as Forum } from 'lucide-react'

const menuItems = {
  employee: [
    { icon: Briefcase, label: 'Трудоустройство', path: '/dashboard/jobs' },
    { icon: FileText, label: 'Резюме', path: '/dashboard/resume' },
    { icon: Map, label: 'Карта возможностей', path: '/dashboard/map' },        { icon: MessageCircle, label: 'Форум и поддержка', path: '/dashboard/community' },
    { icon: User, label: 'Профиль и подписка', path: '/dashboard/profile' },
  ],
  employer: [
    { icon: Briefcase, label: 'Разместить вакансию', path: '/dashboard/post-job' },
    { icon: FileText, label: 'Резюме', path: '/dashboard/resumes' },        { icon: MessageCircle, label: 'Форум и поддержка', path: '/dashboard/community' },
    { icon: MessageCircle, label: 'Форум и поддержка', path: '/dashboard/community' },
    { icon: User, label: 'Профиль и подписка', path: '/dashboard/profile' },
  ],
}

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const user = useStore((state) => state.user)
  const setUser = useStore((state) => state.setUser)

  if (!user) return null

  const items = menuItems[user.type as 'employee' | 'employer'] || []

  const handleLogout = () => {
    setUser(null)
    router.push('/')
  }

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-primary text-white rounded-lg"
      >
        {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-screen fixed left-0 top-0 flex flex-col z-40 transition-transform md:translate-x-0 ${
        mobileOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
      {/* Logo */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div>
            <div className="font-bold text-lg">VECTOR AI</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Инклюзивная платформа
            </div>
          </div>
        </div>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {items.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.path
          
          return (
            <motion.button
              key={item.path}
              onClick={() => {
                router.push(item.path)
                setMobileOpen(false)
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </motion.button>
          )
        })}
        
        {/* Online Interview (Premium) */}
        {user.subscription !== 'none' && (
          <motion.button
            onClick={() => {
              router.push('/dashboard/interview')
              setMobileOpen(false)
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              pathname === '/dashboard/interview'
                ? 'bg-primary text-white'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Video className="w-5 h-5" />
            <span className="font-medium">Онлайн собеседование</span>
          </motion.button>
        )}
      </nav>

      {/* Logout Button */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Выйти из профиля</span>
        </button>
      </div>
      </div>
    </>
  )
}