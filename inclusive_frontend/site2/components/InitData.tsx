'use client'

import { useEffect } from 'react'
import { useStore } from '@/lib/store'
import { seedJobs } from '@/lib/seed'

export function InitData() {
  const jobs = useStore((state) => state.jobs)
  const addJob = useStore((state) => state.addJob)

  useEffect(() => {
    // Initialize demo jobs if empty
    if (jobs.length === 0) {
      seedJobs.forEach((job) => {
        addJob(job)
      })
    }
  }, [jobs.length, addJob])

  return null
}