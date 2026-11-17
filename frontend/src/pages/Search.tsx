import { useState } from 'react'

interface SearchResult {
  id: string
  document_id: string
  text: string
  metadata: { quality_score: number; language?: string }
}

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const [isSearching, setIsSearching] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setIsSearching(true)
    setError('')
    try {
      const response = await fetch('/api/search/semantic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() }),
      })
      if (!response.ok) throw new Error('Search failed')
      const data = await response.json()
      setResults(data.results)
      setTotal(data.total_count)
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl animate-[fadeIn_420ms_ease-out]">
      <div className="mb-6 rounded-2xl border border-[#dfe6df] bg-white/85 p-6 shadow-[0_18px_50px_rgba(23,33,43,0.05)]">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#167c78]">Retrieval desk</p>
        <h2 className="mb-1 font-serif text-2xl font-semibold text-[#17212b]">Find a passage</h2>
        <p className="mb-5 text-sm text-[#718078]">Search extracted and processed document passages.</p>
        <form className="flex gap-3" onSubmit={(event) => { event.preventDefault(); void search() }}>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your documents" className="min-w-0 flex-1 rounded-md border border-[#cbd8d1] bg-[#f8faf8] px-3 py-3 text-sm outline-none transition focus:border-[#167c78] focus:ring-2 focus:ring-[#167c78]/15" />
          <button type="submit" disabled={isSearching || !query.trim()} className="rounded-md bg-[#17212b] px-5 py-2 text-sm font-semibold text-white disabled:bg-[#b9c4bd]">
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>
      <div className="space-y-3">
        {total > 0 && <p className="text-sm text-gray-600">{total} matching chunks</p>}
        {results.map((result) => (
          <article key={result.id} className="rounded-2xl border border-[#dfe6df] bg-white/85 p-5 shadow-[0_12px_30px_rgba(23,33,43,0.04)]">
            <p className="text-sm leading-6 text-[#34443d]">{result.text}</p>
            <p className="mt-3 text-xs font-medium uppercase tracking-wider text-[#718078]">Document {result.document_id} · Quality {result.metadata.quality_score.toFixed(2)}</p>
          </article>
        ))}
      </div>
    </div>
  )
}
