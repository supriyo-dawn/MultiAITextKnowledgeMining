<<<<<<< HEAD
import { useKnowledge } from '../context/KnowledgeContext'

const modeLabels = ['semantic', 'hybrid', 'entities', 'relationships'] as const

export default function Search() {
  const { searchQuery, searchMode, searchResults, setSearchQuery, setSearchMode } = useKnowledge()

  return (
    <div className="space-y-6">
      <div className="rounded-[28px] border border-[#d9d0c5] bg-[#fffaf4] p-6 md:p-8">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[#72685c]">Search</p>
        <h2 className="editorial-display mt-2 text-4xl text-[#171513]">Semantic retrieval</h2>
      </div>

      <div className="rounded-[28px] border border-[#d9d0c5] bg-[#ffffff] p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex-1 rounded-full border border-[#d8cbb9] bg-[#faf7f3] px-4 py-3">
            <input
              aria-label="Search the knowledge graph"
              className="w-full bg-transparent text-base text-[#171513] outline-none placeholder:text-[#72685c]"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search the corpus or graph"
            />
          </div>

          <button onClick={() => setSearchQuery(searchQuery.trim())} className="rounded-full bg-[#171513] px-5 py-3 text-sm font-medium text-[#f7f3ee]">
            Search corpus
          </button>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {modeLabels.map((label) => (
            <button
              key={label}
              onClick={() => setSearchMode(label)}
              className={[
                'rounded-full border px-3 py-1.5 text-[11px] uppercase tracking-[0.18em]',
                searchMode === label
                  ? 'border-[#d1af8a] bg-[#f9f2ea] text-[#171513]'
                  : 'border-[#d8cbb9] bg-[#f7f3ee] text-[#4d4540]',
              ].join(' ')}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {searchResults.length === 0 ? (
          <div className="rounded-[28px] border border-dashed border-[#d9d0c5] bg-[#ffffff] p-6 text-sm text-[#5f564f]">
            No results match the current query. Try searching for pricing, strategy, operations, or risk.
          </div>
        ) : (
          searchResults.map((result) => (
            <article key={result.id} className="rounded-[28px] border border-[#d9d0c5] bg-[#ffffff] p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.2em] text-[#72685c]">{result.source}</p>
                  <h3 className="mt-2 text-2xl font-semibold text-[#171513]">{result.title}</h3>
                </div>

                <div className="rounded-full bg-[#eef5ef] px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-[#3d6c43]">
                  Match {result.score}
                </div>
              </div>

              <p className="mt-4 max-w-3xl text-base leading-7 text-[#4a433d]">{result.excerpt}</p>
              <div className="mt-5 flex flex-wrap items-center gap-3 text-sm text-[#5f564f]">
                <span className="rounded-full border border-[#d8cbb9] bg-[#faf7f3] px-3 py-1.5">{result.kind}</span>
                <span className="rounded-full border border-[#d8cbb9] bg-[#faf7f3] px-3 py-1.5">source-backed</span>
                <span className="rounded-full border border-[#d8cbb9] bg-[#faf7f3] px-3 py-1.5">evidence</span>
              </div>
            </article>
          ))
        )}
=======
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
>>>>>>> ef391a4 (Complete knowledge mining MVP and refresh frontend)
      </div>
    </div>
  )
}
