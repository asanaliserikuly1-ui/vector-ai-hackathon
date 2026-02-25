'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function SupportRedirect(){
  const router = useRouter()
  useEffect(()=>{ router.replace('/dashboard/community') }, [router])
  return null
}