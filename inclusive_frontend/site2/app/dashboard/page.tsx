'use client'

import { useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { useEffect } from 'react'

export default function DashboardPage() {
  const router = useRouter()
  const user = useStore((state) => state.user)

  useEffect(() => {
    if (user) {
      if (user.type === 'employee') {
        router.push('/dashboard/jobs')
      } else {
        router.push('/dashboard/post-job')
      }
    }
  }, [user, router])

  return null
}