'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ForumRedirect(){
  const router = useRouter()
  useEffect(()=>{ router.replace('/dashboard/community') }, [router])
  return null
}