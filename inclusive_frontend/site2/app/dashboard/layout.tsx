'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { AIAssistant } from '@/components/AIAssistant'
import { InitData } from '@/components/InitData'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const user = useStore((state) => state.user)

  useEffect(() => {
    if (!user) {
      router.push('/login')
    }
  }, [user, router])

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-bg-light dark:bg-bg-dark">
      <InitData />
      <Sidebar />
      <div className="pt-16 md:ml-64">
        <Header />
        <main className="p-4 md:p-6">{children}</main>
      </div>
      <AIAssistant />
    </div>
  )
}