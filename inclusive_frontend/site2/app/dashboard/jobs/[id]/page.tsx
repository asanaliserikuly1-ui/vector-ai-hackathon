'use client'

import { useParams, useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { MapPin, DollarSign, Clock, ArrowLeft, Phone, Mail } from 'lucide-react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const jobs = useStore((state) => state.jobs)
  const addApplication = useStore((state) => state.addApplication)
  const user = useStore((state) => state.user)

  const jobId = Array.isArray(params.id) ? params.id[0] : params.id
  const job = jobs.find((j) => j.id === jobId)

  if (!job) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">Вакансия не найдена</p>
      </div>
    )
  }

  const handleApply = () => {
    if (!user) return
    
    const resume = useStore.getState().resumes.find(r => r.userId === user.id)
    if (!resume) {
      toast.error('Сначала создайте резюме')
      router.push('/dashboard/resume')
      return
    }

    const application = {
      id: Date.now().toString(),
      jobId: job.id,
      userId: user.id,
      resumeId: resume.id,
      status: 'pending' as const,
      createdAt: new Date(),
    }

    addApplication(application)
    toast.success('Заявка отправлена!')
  }

  const handleShowOnMap = () => {
    router.push(`/dashboard/map?job=${job.id}`)
  }

  const formatLabels = {
    remote: 'Удалённо',
    office: 'Офис',
    hybrid: 'Гибрид',
  }

  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-primary mb-6 hover:underline"
      >
        <ArrowLeft className="w-5 h-5" />
        Назад к вакансиям
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg"
      >
        <h1 className="text-3xl font-bold mb-2">{job.title}</h1>
        <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-6">
          <span className="font-medium text-lg">{job.company}</span>
          <span>•</span>
          <span>{job.location}</span>
          <span>•</span>
          <span>{formatLabels[job.format]}</span>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-primary" />
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Зарплата</div>
              <div className="font-semibold text-lg">〒 {job.salary.toLocaleString()}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Тип занятости</div>
              <div className="font-semibold">{job.employmentType}</div>
            </div>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">Описание</h2>
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
            {job.description}
          </p>
        </div>

        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">Требования</h2>
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
            {job.requirements}
          </p>
        </div>

        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">Опыт</h2>
          <p className="text-gray-700 dark:text-gray-300">{job.experience}</p>
        </div>

        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">Особенности</h2>
          <div className="flex flex-wrap gap-2">
            {job.features.map((feature, i) => (
              <span
                key={i}
                className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>

        {(job.managerContact || job.callCenterContact) && (
          <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <h2 className="text-xl font-semibold mb-3">Контакты</h2>
            {job.managerContact && (
              <div className="flex items-center gap-2 mb-2">
                <Phone className="w-4 h-4" />
                <span>Менеджер: {job.managerContact}</span>
              </div>
            )}
            {job.callCenterContact && (
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                <span>Call-центр: {job.callCenterContact}</span>
              </div>
            )}
          </div>
        )}

        {job.address && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-primary" />
              <span className="font-semibold">Адрес: {job.address}</span>
            </div>
            <button
              onClick={handleShowOnMap}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              Показать на карте
            </button>
          </div>
        )}

        <div className="flex gap-4 mt-8">
          <button
            onClick={handleApply}
            className="flex-1 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
          >
            Откликнуться
          </button>
        </div>
      </motion.div>
    </div>
  )
}