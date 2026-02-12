import { Video } from '@/types/data'

interface VideoCardProps {
  video: Video
}

export default function VideoCard({ video }: VideoCardProps) {
  const score = video.analysis?.urgency_score || 0
  
  let badgeClass = 'unknown'
  if (score >= 8) badgeClass = 'high'
  else if (score >= 5) badgeClass = 'med'
  else if (score > 0) badgeClass = 'low'

  return (
    <div className="card">
      <div className="header">
        <a href={video.link} target="_blank" rel="noopener noreferrer" className="title">
          عنوان خبر: "{video.title}"
        </a>
        <span className={`badge ${badgeClass}`}>
          خطر: {score}/10
        </span>
      </div>
      <div className="grid">
        <div className="item">
          <span className="label">القای حسی</span>
          <span className="value">{video.analysis?.viewer_emotion || 'N/A'}</span>
        </div>
        <div className="item">
          <span className="label">انتظار مخاطب</span>
          <span className="value">{video.analysis?.viewer_expectation || 'N/A'}</span>
        </div>
        <div className="item">
          <span className="label">هدف رفتاری</span>
          <span className="value">{video.analysis?.call_to_action || 'N/A'}</span>
        </div>
        <div className="item">
          <span className="label">روایت معکوس</span>
          <span className="value">{video.analysis?.defensive_counter_narrative || 'N/A'}</span>
        </div>
      </div>
    </div>
  )
}
