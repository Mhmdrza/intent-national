export interface Analysis {
  urgency_score?: number
  viewer_emotion?: string
  viewer_expectation?: string
  call_to_action?: string
  defensive_counter_narrative?: string
}

export interface Video {
  title: string
  link: string
  published_at: string
  analysis?: Analysis
}

export interface ProcessedData {
  last_updated: string
  videos: Video[]
}
