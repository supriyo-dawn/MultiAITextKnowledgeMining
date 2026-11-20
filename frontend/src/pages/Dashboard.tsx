import { useEffect, useState } from 'react'
import { API_BASE_URL } from '../services/api'

interface AnalyticsSummary {
  documents: { total: number; by_status: Record<string, number> }
  chunks: { total_chunks: number; avg_quality_score: number }
  entities: { total: number; available: boolean }
  relationships: { total: number; available: boolean }
  embeddings: { total: number; available: boolean }
}

export default function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_BASE_URL}/analytics/summary`)
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load analytics')
        return response.json() as Promise<AnalyticsSummary>
      })
      .then(setSummary)
      .catch((loadError: Error) => setError(loadError.message))
  }, [])

  const cards = summary
    ? [
        { title: 'Documents', value: summary.documents.total.toString(), detail: `${summary.documents.by_status.COMPLETED || 0} completed` },
        { title: 'Chunks', value: summary.chunks.total_chunks.toString(), detail: `Quality ${summary.chunks.avg_quality_score.toFixed(2)}` },
        { title: 'Entities', value: summary.entities.total.toString(), detail: 'Locally extracted' },
        { title: 'Relationships', value: summary.relationships.total.toString(), detail: 'Locally extracted' },
      ]
    : null

  return (
    <div className="mx-auto max-w-6xl animate-[fadeIn_420ms_ease-out]">
      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-4">
        {cards?.map((card) => <Card key={card.title} {...card} />) || <p className="text-sm text-gray-600">Loading analytics...</p>}
      </div>

      <div className="rounded-2xl border border-[#dfe6df] bg-white/80 p-6 shadow-[0_18px_50px_rgba(23,33,43,0.06)]">
        <h2 className="mb-4 font-serif text-2xl font-semibold text-[#17212b]">System status</h2>
        {error ? <p className="text-sm text-red-600">{error}</p> : (
          <div className="space-y-2 text-sm text-gray-600">
            <p>Document ingestion: <span className="font-medium text-green-700">Available</span></p>
            <p>Chunk search: <span className="font-medium text-green-700">Available</span></p>
            <p>Knowledge graph: <span className="font-medium text-green-700">Local graph available</span></p>
          </div>
        )}
      </div>
    </div>
  )
}

interface CardProps {
  title: string
  value: string
  detail: string
}

function Card({ title, value, detail }: CardProps) {
  return (
    <div className="rounded-2xl border border-[#dfe6df] bg-white/85 p-6 shadow-[0_18px_50px_rgba(23,33,43,0.05)] transition-transform duration-200 hover:-translate-y-1">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#718078]">{title}</p>
      <p className="mt-3 font-serif text-4xl font-semibold tracking-tight text-[#17212b]">{value}</p>
      <p className="mt-2 text-xs text-[#718078]">{detail}</p>
    </div>
  )
}
