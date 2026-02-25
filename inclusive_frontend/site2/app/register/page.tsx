'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const router = useRouter()
  const setUser = useStore((state) => state.setUser)
  const [userType, setUserType] = useState<'employee' | 'employer' | null>(null)
  const [formData, setFormData] = useState({
    fullName: '',
    phone: '',
    email: '',
    password: '',
    confirmPassword: '',
    healthNeeds: '',
    companyName: '',
    companyDescription: '',
    licenseFile: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (formData.password !== formData.confirmPassword) {
      toast.error('Пароли не совпадают')
      return
    }

    if (!userType) {
      toast.error('Выберите тип пользователя')
      return
    }

    const newUser = {
      id: Date.now().toString(),
      type: userType,
      fullName: formData.fullName,
      phone: formData.phone,
      email: formData.email,
      subscription: 'none' as const,
      createdAt: new Date(),
      ...(userType === 'employee' && { healthNeeds: formData.healthNeeds }),
      ...(userType === 'employer' && {
        companyName: formData.companyName,
        companyDescription: formData.companyDescription,
        licenseFile: formData.licenseFile,
      }),
    }

    setUser(newUser)
    toast.success('Регистрация успешна!')
    router.push('/dashboard')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setFormData({ ...formData, licenseFile: reader.result as string })
      }
      reader.readAsDataURL(file)
    }
  }

  return (
    <div className="min-h-screen bg-bg-light dark:bg-bg-dark flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl"
      >
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-primary mb-6 hover:underline"
        >
          <ArrowLeft className="w-5 h-5" />
          На главную
        </Link>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-8">
          <h1 className="text-3xl font-bold mb-2">Регистрация</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Выберите тип аккаунта
          </p>

          {/* User Type Selection */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => setUserType('employee')}
              className={`p-4 rounded-lg border-2 transition-all ${
                userType === 'employee'
                  ? 'border-primary bg-primary/10'
                  : 'border-gray-300 dark:border-gray-600 hover:border-primary/50'
              }`}
            >
              <div className="text-2xl mb-2">👤</div>
              <div className="font-semibold">Сотрудник</div>
            </button>
            <button
              onClick={() => setUserType('employer')}
              className={`p-4 rounded-lg border-2 transition-all ${
                userType === 'employer'
                  ? 'border-primary bg-primary/10'
                  : 'border-gray-300 dark:border-gray-600 hover:border-primary/50'
              }`}
            >
              <div className="text-2xl mb-2">🏢</div>
              <div className="font-semibold">Работодатель</div>
            </button>
          </div>

          {userType && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Common Fields */}
              <div>
                <label className="block text-sm font-medium mb-2">ФИО</label>
                <input
                  type="text"
                  required
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Номер телефона</label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Почта</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Employee Specific */}
              {userType === 'employee' && (
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Особенности здоровья и потребности
                  </label>
                  <textarea
                    value={formData.healthNeeds}
                    onChange={(e) => setFormData({ ...formData, healthNeeds: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              )}

              {/* Employer Specific */}
              {userType === 'employer' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">Название компании</label>
                    <input
                      type="text"
                      required
                      value={formData.companyName}
                      onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Описание компании</label>
                    <textarea
                      required
                      value={formData.companyDescription}
                      onChange={(e) => setFormData({ ...formData, companyDescription: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Лицензия (PDF)</label>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileChange}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                </>
              )}

              {/* Password Fields */}
              <div>
                <label className="block text-sm font-medium mb-2">Создание пароля</label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Подтверждение пароля</label>
                <input
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <button
                type="submit"
                className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
              >
                Зарегистрироваться
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-gray-600 dark:text-gray-400">
            Уже есть аккаунт?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Войти
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}