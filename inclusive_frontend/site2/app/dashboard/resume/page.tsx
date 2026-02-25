'use client'

import { useState, useRef } from 'react'
import { useStore } from '@/lib/store'
import { motion } from 'framer-motion'
import { Upload, Download, Sparkles, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { generateResume } from '@/lib/api'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

export default function ResumePage() {
  const user = useStore((state) => state.user)
  const addResume = useStore((state) => state.addResume)
  const resume = useStore((state) => state.resumes.find(r => r.userId === user?.id))
  
  const [pdfFile, setPdfFile] = useState<string | null>(null)
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [formData, setFormData] = useState({
    fullName: user?.fullName || '',
    skills: '',
    experience: '',
    description: '',
  })
  const [generatedResume, setGeneratedResume] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPdfFile(reader.result as string)
      }
      reader.readAsDataURL(file)
    } else {
      toast.error('Пожалуйста, загрузите PDF файл')
    }
  }

  const handleSubmitPDF = () => {
    if (!pdfFile || !user) return

    const newResume = {
      id: Date.now().toString(),
      userId: user.id,
      fileUrl: pdfFile,
      fullName: user.fullName,
      skills: [],
      experience: '',
      description: '',
      createdAt: new Date(),
    }

    addResume(newResume)
    toast.success('Резюме загружено и отправлено в профиль!')
    setPdfFile(null)
  }

  const handleGenerateResume = async () => {
    if (!formData.fullName || !formData.skills || !formData.experience) {
      toast.error('Заполните все поля')
      return
    }

    setIsGenerating(true)
    try {
      const generated = await generateResume(formData)
      setGeneratedResume(generated)
      
      if (user) {
        const newResume = {
          id: Date.now().toString(),
          userId: user.id,
          fullName: formData.fullName,
          skills: formData.skills.split(',').map(s => s.trim()),
          experience: formData.experience,
          description: formData.description,
          generatedContent: generated,
          createdAt: new Date(),
        }

        addResume(newResume)
        toast.success('Резюме сгенерировано и отправлено в профиль!')
      }
    } catch (error) {
      toast.error('Ошибка при генерации резюме')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownloadPDF = () => {
    if (!generatedResume) return

    // Simple PDF generation using browser print
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Резюме - ${formData.fullName}</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; }
              h1 { color: #ff8c00; }
              h2 { color: #333; margin-top: 20px; }
            </style>
          </head>
          <body>
            ${generatedResume.replace(/\n/g, '<br>')}
          </body>
        </html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Резюме</h1>

      {/* PDF Upload Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg mb-6"
      >
        <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-6 h-6" />
          Загрузка PDF резюме
        </h2>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          className="hidden"
        />

        {!pdfFile ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center cursor-pointer hover:border-primary transition-colors"
          >
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600 dark:text-gray-400">
              Нажмите для загрузки PDF файла
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="border rounded-lg p-4 bg-gray-50 dark:bg-gray-700">
              <Document
                file={pdfFile}
                onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                loading={<div>Загрузка PDF...</div>}
              >
                <Page pageNumber={pageNumber} width={600} />
              </Document>
              {numPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <button
                    onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-600 rounded"
                    disabled={pageNumber <= 1}
                  >
                    Назад
                  </button>
                  <span>
                    Страница {pageNumber} из {numPages}
                  </span>
                  <button
                    onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-600 rounded"
                    disabled={pageNumber >= numPages}
                  >
                    Вперёд
                  </button>
                </div>
              )}
            </div>
            <div className="flex gap-4">
              <button
                onClick={handleSubmitPDF}
                className="flex-1 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors"
              >
                Отправить резюме
              </button>
              <button
                onClick={() => {
                  setPdfFile(null)
                  setPageNumber(1)
                }}
                className="px-6 py-3 bg-gray-200 dark:bg-gray-600 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
              >
                Удалить
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Resume Generator Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg"
      >
        <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
          <Sparkles className="w-6 h-6" />
          Генератор резюме
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">ФИО *</label>
            <input
              type="text"
              required
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Навыки (через запятую) *</label>
            <input
              type="text"
              required
              value={formData.skills}
              onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
              placeholder="Например: JavaScript, React, TypeScript"
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Опыт работы *</label>
            <textarea
              required
              value={formData.experience}
              onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
              rows={4}
              placeholder="Опишите ваш опыт работы..."
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">О себе</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              placeholder="Расскажите о себе..."
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <button
            onClick={handleGenerateResume}
            disabled={isGenerating}
            className="w-full py-3 bg-primary text-white rounded-lg font-semibold hover:bg-orange-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            {isGenerating ? 'Генерация резюме...' : 'Сгенерировать резюме'}
          </button>

          {generatedResume && (
            <div className="mt-6 p-6 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Сгенерированное резюме</h3>
                <button
                  onClick={handleDownloadPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-orange-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Скачать PDF
                </button>
              </div>
              <div className="whitespace-pre-line text-gray-700 dark:text-gray-300">
                {generatedResume}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}