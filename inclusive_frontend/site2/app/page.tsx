'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { ArrowDown, Mail, Phone, MapPin } from 'lucide-react'
import Link from 'next/link'

export default function HomePage() {
  const router = useRouter()
  const user = useStore((state) => state.user)

  useEffect(() => {
    if (user) {
      router.push('/dashboard')
    }
  }, [user, router])

  return (
    <div className="min-h-screen bg-bg-light dark:bg-bg-dark text-gray-900 dark:text-white">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-primary/10 to-transparent" />
        
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10 text-center px-4 max-w-4xl mx-auto"
        >
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-8"
          >

            <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-primary to-orange-600 bg-clip-text text-transparent">
              VECTOR AI
            </h1>
            <p className="text-lg sm:text-2xl md:text-3xl text-gray-700 dark:text-gray-300 mb-2">
              Инклюзивная платформа
            </p>
            <p className="text-base sm:text-lg md:text-xl text-gray-600 dark:text-gray-400">
              Подбор работы под ваши особенности
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mt-8"
          >
            <Link
              href="/register"
              className="px-6 md:px-8 py-3 md:py-4 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors shadow-lg hover:shadow-xl text-sm md:text-base"
            >
              Начать работу
            </Link>
            <Link
              href="/login"
              className="px-6 md:px-8 py-3 md:py-4 bg-transparent border-2 border-primary text-primary dark:text-white rounded-lg font-semibold hover:bg-primary hover:text-white transition-colors text-sm md:text-base"
            >
              Войти
            </Link>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, repeat: Infinity, repeatType: 'reverse', duration: 1.5 }}
          className="absolute bottom-10 left-1/2 transform -translate-x-1/2"
        >
          <ArrowDown className="w-8 h-8 text-primary animate-bounce" />
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-12 md:py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold text-center mb-8 md:mb-12"
          >
            Наши возможности
          </motion.h2>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6 md:gap-8">
            {[
              {
                title: 'Умный подбор вакансий',
                description: 'AI учитывает ваши особенности и подбирает подходящие вакансии',
                icon: '🎯',
              },
              {
                title: 'Генератор резюме',
                description: 'Создайте профессиональное резюме с помощью искусственного интеллекта',
                icon: '📝',
              },
              {
                title: 'Инклюзивные работодатели',
                description: 'Только проверенные компании с комфортными условиями',
                icon: '🤝',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="p-6 rounded-xl bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-12 md:py-20 px-4 bg-gray-100 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto text-center">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold mb-8 md:mb-12"
          >
            Наши контакты
          </motion.h2>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6 md:gap-8">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center"
            >
              <Phone className="w-8 h-8 text-primary mb-4" />
              <p className="font-semibold mb-2">Телефон</p>
              <p className="text-gray-600 dark:text-gray-400">+7 (XXX) XXX-XX-XX</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="flex flex-col items-center"
            >
              <Mail className="w-8 h-8 text-primary mb-4" />
              <p className="font-semibold mb-2">Email</p>
              <p className="text-gray-600 dark:text-gray-400">info@tenai.kz</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex flex-col items-center"
            >
              <MapPin className="w-8 h-8 text-primary mb-4" />
              <p className="font-semibold mb-2">Адрес</p>
              <p className="text-gray-600 dark:text-gray-400">Алматы, Казахстан</p>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  )
}