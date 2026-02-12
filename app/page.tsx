'use client'

import { useEffect, useState } from 'react'
import VideoCard from '@/components/VideoCard'
import { ProcessedData } from '@/types/data'
import './page.css'

export default function Home() {
  const [data, setData] = useState<ProcessedData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/data')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch data')
        return res.json()
      })
      .then((data) => {
        setData(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="container">
        <div className="loading">در حال بارگذاری...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">خطا در بارگذاری داده‌ها: {error}</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="container">
        <div className="error">داده‌ای یافت نشد</div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1>رادار تحلیل جنگ شناختی</h1>
      <p className="last-updated">آخرین بروزرسانی: {data.last_updated}</p>
      
      {data.videos.length === 0 ? (
        <div className="empty">هیچ ویدیوی تحلیل‌شده‌ای وجود ندارد</div>
      ) : (
        data.videos.map((video, index) => (
          <VideoCard key={index} video={video} />
        ))
      )}
    </div>
  )
}
