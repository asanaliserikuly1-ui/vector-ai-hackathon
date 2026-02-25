'use client'

import { Moon, Sun } from 'lucide-react'
import { useTheme } from './ThemeProvider'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-transparent hover:bg-opacity-10 transition-colors"
    >
      {theme === 'dark' ? (
        <>
          <Moon className="w-5 h-5 text-primary" />
          <span className="text-sm font-medium dark:text-white text-gray-800">Тёмная</span>
        </>
      ) : (
        <>
          <Sun className="w-5 h-5 text-primary" />
          <span className="text-sm font-medium text-gray-800">Светлая</span>
        </>
      )}
    </button>
  )
}