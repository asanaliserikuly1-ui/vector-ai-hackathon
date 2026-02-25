'use client'

import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { Video, Lock } from 'lucide-react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function InterviewPage() {
  const user = useStore((state) => state.user)
  const router = useRouter()
  const hasPremium = user?.subscription !== 'none'

  if (!hasPremium) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-12 shadow-lg"
        >
          <Lock className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">Премиум функция</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Для доступа к онлайн собеседованию необходимо оформить премиум подписку
          </p>
          <button
            onClick={() => router.push('/dashboard/profile')}
            className="px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
          >
            Перейти к подписке
          </button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Онлайн собеседование</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg"
      >
        <div className="text-center mb-8">
          <Video className="w-16 h-16 mx-auto mb-4 text-primary" />
          <h2 className="text-2xl font-semibold mb-2">Подготовка к собеседованию</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Здесь будет интегрирована система видеосвязи для проведения онлайн собеседований
          </p>
        </div>

        <div className="space-y-4">
          <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <h3 className="font-semibold mb-2">Функции:</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
              <li>Видео и аудио связь в реальном времени</li>
              <li>Текстовая переписка во время собеседования</li>
              <li>Запись собеседования (с согласия сторон)</li>
              <li>Доступность для людей с ограниченными возможностями</li>
            </ul>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => toast('Функция в разработке')}
              className="flex-1 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
            >
              Начать собеседование
            </button>
            <button
              onClick={() => toast('Функция в разработке')}
              className="px-6 py-3 bg-gray-200 dark:bg-gray-600 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
            >
              Расписание
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}