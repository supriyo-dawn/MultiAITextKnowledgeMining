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
      </div>
    </div>
  )
}
