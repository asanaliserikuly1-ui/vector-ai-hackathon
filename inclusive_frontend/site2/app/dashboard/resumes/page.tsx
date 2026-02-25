'use client'

import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, FileText } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function ResumesPage() {
  const resumes = useStore((state) => state.resumes)
  const updateApplicationStatus = useStore((state) => state.updateApplicationStatus)
  const applications = useStore((state) => state.applications)
  const [selectedResume, setSelectedResume] = useState<string | null>(null)

  const resume = resumes.find(r => r.id === selectedResume)

  const handleAccept = (resumeId: string) => {
    const application = applications.find(app => app.resumeId === resumeId)
    if (application) {
      updateApplicationStatus(application.id, 'accepted')
      toast.success('Резюме принято!')
    }
  }

  const handleReject = (resumeId: string) => {
    const application = applications.find(app => app.resumeId === resumeId)
    if (application) {
      updateApplicationStatus(application.id, 'rejected')
      toast.success('Резюме отклонено')
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Резюме в базе</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Resume List */}
        <div className="lg:col-span-1 space-y-4">
          {resumes.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center">
              <p className="text-gray-600 dark:text-gray-400">
                Пока нет резюме в базе
              </p>
            </div>
          ) : (
            resumes.map((r, index) => (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => setSelectedResume(r.id)}
                className={`p-4 bg-white dark:bg-gray-800 rounded-xl shadow-lg cursor-pointer hover:shadow-xl transition-shadow ${
                  selectedResume === r.id ? 'ring-2 ring-primary' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-8 h-8 text-primary" />
                  <div>
                    <h3 className="font-semibold">{r.fullName}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {r.skills.slice(0, 3).join(', ')}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>

        {/* Resume Details */}
        <div className="lg:col-span-2">
          {resume ? (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg"
            >
              <h2 className="text-2xl font-bold mb-4">{resume.fullName}</h2>

              {resume.fileUrl ? (
                <div className="mb-6">
                  <p className="text-gray-600 dark:text-gray-400 mb-2">
                    Загруженное резюме (PDF)
                  </p>
                  <a
                    href={resume.fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Открыть PDF
                  </a>
                </div>
              ) : (
                <>
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Навыки</h3>
                    <div className="flex flex-wrap gap-2">
                      {resume.skills.map((skill, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Опыт работы</h3>
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
                      {resume.experience}
                    </p>
                  </div>

                  {resume.description && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-2">О себе</h3>
                      <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
                        {resume.description}
                      </p>
                    </div>
                  )}

                  {resume.generatedContent && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-2">Резюме</h3>
                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
                          {resume.generatedContent}
                        </p>
                      </div>
                    </div>
                  )}
                </>
              )}

              <div className="flex gap-4 mt-8">
                <button
                  onClick={() => handleAccept(resume.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors"
                >
                  <CheckCircle className="w-5 h-5" />
                  Принять
                </button>
                <button
                  onClick={() => handleReject(resume.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                  Отклонить
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-12 text-center">
              <p className="text-gray-600 dark:text-gray-400">
                Выберите резюме для просмотра
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}