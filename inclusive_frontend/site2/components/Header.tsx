'use client'

import { useStore } from '@/lib/store'
import { ThemeToggle } from './ThemeToggle'
import { Info } from 'lucide-react'

export function Header() {
  const user = useStore((state) => state.user)
  const hasPremium = user?.subscription !== 'none'

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 fixed top-0 left-0 right-0 md:left-64 z-10 flex items-center justify-between px-4 md:px-6 md:pl-6">
      <div className="flex-1 pl-12 md:pl-0">
        {user?.type === 'employee' && (
          <h2 className="text-sm md:text-lg font-semibold text-gray-800 dark:text-white">
            Подбор работы под ваши особенности
          </h2>
        )}
      </div>

      <div className="flex items-center gap-4">
        {!hasPremium && (
          <div className="flex items-center gap-2 px-4 py-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
            <Info className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
            <span className="text-sm text-yellow-800 dark:text-yellow-200">
              Некоторые функции пока заблокированы. Оформите подписку в профиле.
            </span>
          </div>
        )}
        <ThemeToggle />
      </div>
    </header>
  )
}