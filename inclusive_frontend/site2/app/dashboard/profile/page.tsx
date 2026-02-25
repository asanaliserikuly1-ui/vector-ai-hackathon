'use client'

import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { Check, Crown, Star, FileText, XCircle, Clock } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const user = useStore((state) => state.user)
  const setUser = useStore((state) => state.setUser)
  const applications = useStore((state) => state.applications)
  const jobs = useStore((state) => state.jobs)
  const resumes = useStore((state) => state.resumes)
  const [editingDescription, setEditingDescription] = useState(false)
  const [companyDescription, setCompanyDescription] = useState(
    user?.companyDescription || ''
  )

  if (!user) return null

  const userResume = resumes.find(r => r.userId === user.id)
  const userApplications = applications.filter(app => app.userId === user.id)

  const handleSubscribe = (type: 'basic' | 'plus') => {
    const endDate = new Date()
    endDate.setDate(endDate.getDate() + (type === 'basic' ? 7 : 30))

    setUser({
      ...user,
      subscription: type,
      subscriptionEndDate: endDate,
    })
    toast.success(`Подписка ${type === 'basic' ? 'Basic' : 'Plus'} активирована!`)
  }

  const handleSaveDescription = () => {
    if (user.type === 'employer') {
      setUser({
        ...user,
        companyDescription,
      })
      toast.success('Описание сохранено')
      setEditingDescription(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Профиль и подписка</h1>

      {/* User Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg mb-6"
      >
        <h2 className="text-2xl font-semibold mb-4">Личные данные</h2>
        <div className="space-y-3">
          <div>
            <span className="text-gray-600 dark:text-gray-400">ФИО:</span>
            <span className="ml-2 font-medium">{user.fullName}</span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Телефон:</span>
            <span className="ml-2 font-medium">{user.phone}</span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Почта:</span>
            <span className="ml-2 font-medium">{user.email}</span>
          </div>
          {user.type === 'employee' && user.healthNeeds && (
            <div>
              <span className="text-gray-600 dark:text-gray-400">Особенности здоровья:</span>
              <span className="ml-2 font-medium">{user.healthNeeds}</span>
            </div>
          )}
          {user.type === 'employer' && (
            <>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Название компании:</span>
                <span className="ml-2 font-medium">{user.companyName}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Описание компании:</span>
                {editingDescription ? (
                  <div className="mt-2">
                    <textarea
                      value={companyDescription}
                      onChange={(e) => setCompanyDescription(e.target.value)}
                      rows={4}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
                    />
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={handleSaveDescription}
                        className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-orange-700"
                      >
                        Сохранить
                      </button>
                      <button
                        onClick={() => {
                          setCompanyDescription(user.companyDescription || '')
                          setEditingDescription(false)
                        }}
                        className="px-4 py-2 bg-gray-200 dark:bg-gray-600 rounded-lg"
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-2">
                    <p className="font-medium">{user.companyDescription || 'Не указано'}</p>
                    <button
                      onClick={() => setEditingDescription(true)}
                      className="mt-2 text-primary hover:underline text-sm"
                    >
                      Изменить
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* PDF Files */}
        {user.licenseFile && (
          <div className="mt-6">
            <h3 className="font-semibold mb-2">Загруженные файлы</h3>
            <a
              href={user.licenseFile}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-primary hover:underline"
            >
              <FileText className="w-5 h-5" />
              Лицензия (PDF)
            </a>
          </div>
        )}

        {userResume?.fileUrl && (
          <div className="mt-4">
            <a
              href={userResume.fileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-primary hover:underline"
            >
              <FileText className="w-5 h-5" />
              Резюме (PDF)
            </a>
          </div>
        )}
      </motion.div>

      {/* Applications History (for employees) */}
      {user.type === 'employee' && userApplications.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg mb-6"
        >
          <h2 className="text-2xl font-semibold mb-4">История заявок</h2>
          <div className="space-y-3">
            {userApplications.map((app) => {
              const job = jobs.find(j => j.id === app.jobId)
              return (
                <div
                  key={app.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div>
                    <h3 className="font-semibold">{job?.title || 'Вакансия'}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {job?.company} • {new Date(app.createdAt).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {app.status === 'pending' && (
                      <div className="flex items-center gap-2 text-yellow-600">
                        <Clock className="w-5 h-5" />
                        <span>На рассмотрении</span>
                      </div>
                    )}
                    {app.status === 'accepted' && (
                      <div className="flex items-center gap-2 text-green-600">
                        <Check className="w-5 h-5" />
                        <span>Принято</span>
                      </div>
                    )}
                    {app.status === 'rejected' && (
                      <div className="flex items-center gap-2 text-red-600">
                        <XCircle className="w-5 h-5" />
                        <span>Отклонено</span>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Premium Subscriptions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg"
      >
        <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
          <Crown className="w-6 h-6 text-yellow-500" />
          Премиум подписки
        </h2>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Basic Plan */}
          <div className={`border-2 rounded-xl p-6 ${
            user.subscription === 'basic' ? 'border-primary bg-primary/5' : 'border-gray-300 dark:border-gray-600'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Basic</h3>
              {user.subscription === 'basic' && (
                <span className="px-3 py-1 bg-primary text-white rounded-full text-sm">
                  Активна
                </span>
              )}
            </div>
            <div className="text-3xl font-bold mb-4">2 990 ₸</div>
            <ul className="space-y-2 mb-6">
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>7 дней пробный период</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Онлайн собеседование</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Улучшенный AI помощник</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Генерация более четкого резюме</span>
              </li>
            </ul>
            <button
              onClick={() => handleSubscribe('basic')}
              disabled={user.subscription === 'basic'}
              className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors disabled:opacity-50"
            >
              {user.subscription === 'basic' ? 'Активна' : 'Оформить'}
            </button>
          </div>

          {/* Plus Plan */}
          <div className={`border-2 rounded-xl p-6 ${
            user.subscription === 'plus' ? 'border-primary bg-primary/5' : 'border-gray-300 dark:border-gray-600'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Plus</h3>
              {user.subscription === 'plus' && (
                <span className="px-3 py-1 bg-primary text-white rounded-full text-sm">
                  Активна
                </span>
              )}
            </div>
            <div className="text-3xl font-bold mb-4">4 990 ₸</div>
            <ul className="space-y-2 mb-6">
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Выдача именного бейджа</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Сертификация</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Онлайн собеседование</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Все функции Basic</span>
              </li>
            </ul>
            <button
              onClick={() => handleSubscribe('plus')}
              disabled={user.subscription === 'plus'}
              className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors disabled:opacity-50"
            >
              {user.subscription === 'plus' ? 'Активна' : 'Оформить'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}