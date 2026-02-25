'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { generateInclusiveJobDescription } from '@/lib/api'

export default function PostJobPage() {
  const router = useRouter()
  const addJob = useStore((state) => state.addJob)
  const user = useStore((state) => state.user)
  const [isGenerating, setIsGenerating] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    requirements: '',
    experience: '',
    salary: '',
    description: '',
    address: '',
    format: 'remote' as 'remote' | 'office' | 'hybrid',
    tags: '',
    features: [] as string[],
  })

  const featureOptions = [
    'Без звонков',
    'Только текст',
    'Пандус / Лифт',
    'Ассистент',
    'Тихая зона',
    'Удобный график',
    'Поддерживающая команда',
    'Домашний офис',
  ]

  const handleGenerateInclusive = async () => {
    if (!formData.description.trim()) {
      toast.error('Сначала введите описание вакансии')
      return
    }

    setIsGenerating(true)
    try {
      const inclusiveDescription = await generateInclusiveJobDescription(
        formData.description
      )
      setFormData({ ...formData, description: inclusiveDescription })
      toast.success('Описание успешно переписано!')
    } catch (error) {
      toast.error('Ошибка при генерации описания')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) return

    const newJob = {
      id: Date.now().toString(),
      title: formData.title,
      company: user.companyName || 'Компания',
      location: formData.address || 'Не указано',
      format: formData.format,
      salary: Number(formData.salary),
      employmentType: 'полная занятость',
      requirements: formData.requirements,
      experience: formData.experience,
      description: formData.description,
      address: formData.address,
      tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
      features: formData.features,
      employerId: user.id,
      createdAt: new Date(),
    }

    addJob(newJob)
    toast.success('Вакансия размещена!')
    router.push('/dashboard/post-job')
    setFormData({
      title: '',
      requirements: '',
      experience: '',
      salary: '',
      description: '',
      address: '',
      format: 'remote',
      tags: '',
      features: [],
    })
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Разместить вакансию</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Название вакансии *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Требования *</label>
            <textarea
              required
              value={formData.requirements}
              onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
              rows={4}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Опыт работы *</label>
            <input
              type="text"
              required
              value={formData.experience}
              onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
              placeholder="Например: от 1 года"
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Зарплата (тг) *</label>
            <input
              type="number"
              required
              value={formData.salary}
              onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Описание *</label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={6}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {user?.subscription !== 'none' && (
              <button
                type="button"
                onClick={handleGenerateInclusive}
                disabled={isGenerating}
                className="mt-2 flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {isGenerating ? 'Генерация...' : 'Сделать описание инклюзивным (AI)'}
              </button>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Адрес *</label>
            <input
              type="text"
              required
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Формат работы *</label>
            <select
              value={formData.format}
              onChange={(e) => setFormData({ ...formData, format: e.target.value as any })}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="remote">Удалённо</option>
              <option value="office">Офис</option>
              <option value="hybrid">Гибрид</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Теги (через запятую)</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              placeholder="Например: SQL, Excel, Аналитика"
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Особенности для инклюзивных людей</label>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {featureOptions.map((feature) => (
                <label key={feature} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.features.includes(feature)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData({
                          ...formData,
                          features: [...formData.features, feature],
                        })
                      } else {
                        setFormData({
                          ...formData,
                          features: formData.features.filter((f) => f !== feature),
                        })
                      }
                    }}
                    className="w-4 h-4 text-primary focus:ring-primary rounded"
                  />
                  <span>{feature}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
          >
            Разместить вакансию
          </button>
        </form>
      </motion.div>
    </div>
  )
}