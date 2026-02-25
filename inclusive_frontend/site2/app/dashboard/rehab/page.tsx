'use client'

import { motion } from 'framer-motion'
import { MapPin, Phone, Globe } from 'lucide-react'

const rehabCenters = [
  {
    id: '1',
    name: 'Реабилитационный центр "Надежда"',
    address: 'Алматы, ул. Абая, 150',
    phone: '+7 (727) XXX-XX-XX',
    website: 'www.example.kz',
    description: 'Комплексная реабилитация для людей с ограниченными возможностями',
  },
  {
    id: '2',
    name: 'Центр социальной адаптации',
    address: 'Алматы, пр. Достык, 200',
    phone: '+7 (727) XXX-XX-XX',
    website: 'www.example2.kz',
    description: 'Помощь в социальной адаптации и трудоустройстве',
  },
]

export default function RehabPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Реабилитационные центры</h1>

      <div className="grid md:grid-cols-2 gap-6">
        {rehabCenters.map((center, index) => (
          <motion.div
            key={center.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow"
          >
            <h2 className="text-xl font-semibold mb-3">{center.name}</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {center.description}
            </p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-primary" />
                <span>{center.address}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-primary" />
                <span>{center.phone}</span>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary" />
                <span>{center.website}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
