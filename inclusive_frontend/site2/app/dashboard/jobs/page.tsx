'use client'

import { useState, useEffect } from 'react'
import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { MapPin, DollarSign, Clock, CheckCircle } from 'lucide-react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function JobsPage() {
  const router = useRouter()
  const jobs = useStore((state) => state.jobs)
  const addApplication = useStore((state) => state.addApplication)
  const user = useStore((state) => state.user)
  
  const [filters, setFilters] = useState({
    format: 'all' as 'all' | 'remote' | 'office' | 'hybrid',
    features: [] as string[],
    minSalary: 0,
    useGeolocation: false,
  })

  const [userLocation, setUserLocation] = useState<[number, number] | null>(null)

  useEffect(() => {
    if (filters.useGeolocation && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation([position.coords.latitude, position.coords.longitude])
        },
        () => {
          toast.error('Не удалось получить геолокацию')
        }
      )
    }
  }, [filters.useGeolocation])

  const formatLabels = {
    all: 'Все',
    remote: 'Удалённо',
    office: 'Офис',
    hybrid: 'Гибрид',
  }

  const featureOptions = [
    'Без звонков',
    'Только текст',
    'Пандус / Лифт',
    'Ассистент',
    'Тихая зона',
    'Удобный график',
  ]

  const filteredJobs = jobs.filter((job) => {
    if (filters.format !== 'all' && job.format !== filters.format) return false
    if (filters.minSalary > 0 && job.salary < filters.minSalary) return false
    if (filters.features.length > 0) {
      const hasAllFeatures = filters.features.every((feature) =>
        job.features.includes(feature)
      )
      if (!hasAllFeatures) return false
    }
    return true
  })

  const handleApply = (jobId: string) => {
    if (!user) return
    
    const resume = useStore.getState().resumes.find(r => r.userId === user.id)
    if (!resume) {
      toast.error('Сначала создайте резюме')
      router.push('/dashboard/resume')
      return
    }

    const application = {
      id: Date.now().toString(),
      jobId,
      userId: user.id,
      resumeId: resume.id,
      status: 'pending' as const,
      createdAt: new Date(),
    }

    addApplication(application)
    toast.success('Заявка отправлена!')
  }

  const handleViewJob = (jobId: string) => {
    router.push(`/dashboard/jobs/${jobId}`)
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Подходящие вакансии</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Мы учитываем ваши ответы из анкеты и подбираем вакансии с комфортными условиями.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg sticky top-24">
            <h2 className="text-xl font-semibold mb-4">Фильтры</h2>

            {/* Format Filter */}
            <div className="mb-6">
              <h3 className="font-medium mb-3">Формат</h3>
              <div className="space-y-2">
                {(['all', 'remote', 'office', 'hybrid'] as const).map((format) => (
                  <label key={format} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="format"
                      checked={filters.format === format}
                      onChange={() => setFilters({ ...filters, format })}
                      className="w-4 h-4 text-primary focus:ring-primary"
                    />
                    <span>{formatLabels[format]}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Features Filter */}
            <div className="mb-6">
              <h3 className="font-medium mb-3">Особенности</h3>
              <div className="space-y-2">
                {featureOptions.map((feature) => (
                  <label key={feature} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.features.includes(feature)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters({
                            ...filters,
                            features: [...filters.features, feature],
                          })
                        } else {
                          setFilters({
                            ...filters,
                            features: filters.features.filter((f) => f !== feature),
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

            {/* Salary Slider */}
            <div className="mb-6">
              <h3 className="font-medium mb-3">
                Минимальная зарплата: 〒 {filters.minSalary.toLocaleString()}
              </h3>
              <input
                type="range"
                min="0"
                max="1000000"
                step="10000"
                value={filters.minSalary}
                onChange={(e) =>
                  setFilters({ ...filters, minSalary: Number(e.target.value) })
                }
                className="w-full"
              />
            </div>

            {/* Geolocation */}
            <div className="mb-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.useGeolocation}
                  onChange={(e) =>
                    setFilters({ ...filters, useGeolocation: e.target.checked })
                  }
                  className="w-4 h-4 text-primary focus:ring-primary rounded"
                />
                <span>По геолокации</span>
              </label>
            </div>

            <button
              onClick={() => toast.success('Фильтры применены')}
              className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
            >
              Применить
            </button>
          </div>
        </div>

        {/* Job Listings */}
        <div className="lg:col-span-3">
          {filteredJobs.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-12 text-center">
              <p className="text-gray-600 dark:text-gray-400 text-lg">
                Пока нет подходящих вакансий. Попробуйте изменить фильтры.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredJobs.map((job, index) => (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                  onClick={() => handleViewJob(job.id)}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-semibold mb-1">{job.title}</h3>
                      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
                        <span className="font-medium">{job.company}</span>
                        <span>•</span>
                        <span>{job.location}</span>
                        {job.format !== 'office' && (
                          <>
                            <span>•</span>
                            <span className="capitalize">
                              {formatLabels[job.format]}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 mb-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <DollarSign className="w-4 h-4" />
                      <span>〒 {job.salary.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>{job.employmentType}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {job.tags.slice(0, 6).map((tag, i) => (
                      <span
                        key={i}
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          i < 3
                            ? 'bg-primary/20 text-primary'
                            : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                        }`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleApply(job.id)
                    }}
                    className="px-6 py-2 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
                  >
                    Откликнуться
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}