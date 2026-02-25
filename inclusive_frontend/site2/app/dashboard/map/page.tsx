'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { YMaps, Map, Placemark, ZoomControl } from '@pbe/react-yandex-maps'
import { motion } from 'framer-motion'

const YANDEX_MAP_API_KEY = process.env.NEXT_PUBLIC_YANDEX_MAP_API_KEY || ''

export default function MapPage() {
  const router = useRouter()
  const jobs = useStore((state) => state.jobs)
  const user = useStore((state) => state.user)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const jobId = params.get('job')
      if (jobId) {
        setSelectedJobId(jobId)
      }
    }
  }, [])

  // Mock coordinates for Almaty
  const defaultCenter: [number, number] = [43.2220, 76.8512]

  const jobsWithCoordinates = jobs
    .filter((job) => job.address)
    .map((job) => ({
      ...job,
      coordinates: job.coordinates || defaultCenter,
    }))

  const handlePlacemarkClick = (jobId: string) => {
    setSelectedJobId(jobId)
    router.push(`/dashboard/jobs/${jobId}`)
  }

  // Only show for employees
  if (user?.type !== 'employee') {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">
          Эта страница доступна только для сотрудников
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Карта возможностей</h1>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden"
        style={{ height: '600px' }}
      >
        <YMaps query={{ apikey: YANDEX_MAP_API_KEY }}>
          <Map
            defaultState={{
              center: defaultCenter,
              zoom: 12,
            }}
            width="100%"
            height="100%"
            modules={['geocode', 'geolocation']}
          >
            {jobsWithCoordinates.map((job) => (
              <Placemark
                key={job.id}
                geometry={job.coordinates}
                properties={{
                  balloonContentHeader: job.title,
                  balloonContentBody: `${job.company} • ${job.location}`,
                  balloonContentFooter: `<a href="/dashboard/jobs/${job.id}">Подробнее</a>`,
                }}
                options={{
                  preset: 'islands#violetDotIcon',
                }}
                onClick={() => handlePlacemarkClick(job.id)}
              />
            ))}
            <ZoomControl />
          </Map>
        </YMaps>
      </motion.div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {jobsWithCoordinates.map((job) => (
          <motion.div
            key={job.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={() => handlePlacemarkClick(job.id)}
            className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg cursor-pointer hover:shadow-xl transition-shadow"
          >
            <h3 className="font-semibold mb-1">{job.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {job.company} • {job.location}
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}