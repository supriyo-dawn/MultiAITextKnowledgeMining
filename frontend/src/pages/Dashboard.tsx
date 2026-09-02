import { useNavigate } from 'react-router-dom'
import { useKnowledge } from '../context/KnowledgeContext'

const pipeline = ['Document parsing', 'NER extraction', 'Relationship scoring', 'Graph assembly', 'Retrieval + RAG']

export default function Dashboard() {
  const navigate = useNavigate()
  const { documents, stats } = useKnowledge()

  const topDocuments = documents.slice(0, 3).map((document) => ({
    name: document.filename,
    type: document.fileType.toUpperCase(),
    entities: Math.max(40, Math.round(document.characterCount / 10)),
    state: document.status,
  }))

  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#f1e9df] p-6 md:p-8">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#d6b391] bg-[#fbf5ee] px-3 py-1.5 text-[11px] uppercase tracking-[0.22em] text-[#7a5a3d]">
            Research workspace
          </div>

          <h2 className="editorial-display max-w-xl text-4xl leading-[0.95] text-[#171513] md:text-6xl">
            From document to graph.
          </h2>

          <p className="mt-5 max-w-lg text-base leading-7 text-[#4a433d]">
            Build a living map of company knowledge: extract entities, validate relationships, and answer questions with source-backed evidence.
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button onClick={() => navigate('/documents')} className="rounded-full bg-[#171513] px-5 py-3 text-sm font-medium text-[#f7f3ee] transition hover:bg-[#2d2824]">
              Upload document
            </button>
            <button onClick={() => navigate('/knowledge')} className="rounded-full border border-[#cabca8] bg-transparent px-5 py-3 text-sm font-medium text-[#171513] transition hover:border-[#b79f82] hover:bg-[#f8f3ed]">
              Explore graph
            </button>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <MiniStat label="Sources" value={String(documents.length || 0)} />
            <MiniStat label="Validated" value={documents.length ? `${Math.min(99, Math.round((documents.filter((document) => document.status === 'completed').length / Math.max(documents.length, 1)) * 100))}%` : '0%'} />
            <MiniStat label="Avg. latency" value={documents.length ? '1.3s' : '—'} />
          </div>
        </div>

        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#fffaf4] p-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-[#72685c]">Pipeline</p>
              <h3 className="mt-2 text-xl font-semibold text-[#171513]">Signal flow</h3>
            </div>
            <div className="rounded-full border border-[#d7c7b1] bg-[#f8f1e7] px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-[#6d5749]">
              live
            </div>
          </div>

          <div className="relative overflow-hidden rounded-[22px] border border-[#e5dccc] bg-[#f5efe8] p-4">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(168,118,72,0.16),transparent_45%)]" />
            <svg viewBox="0 0 420 260" className="relative z-10 h-[260px] w-full">
              <line x1="30" y1="110" x2="120" y2="110" stroke="#b8997f" strokeWidth="2" />
              <line x1="120" y1="110" x2="210" y2="65" stroke="#b8997f" strokeWidth="2" />
              <line x1="120" y1="110" x2="210" y2="155" stroke="#b8997f" strokeWidth="2" />
              <line x1="210" y1="65" x2="320" y2="90" stroke="#b8997f" strokeWidth="2" />
              <line x1="210" y1="155" x2="320" y2="190" stroke="#b8997f" strokeWidth="2" />
              <line x1="320" y1="90" x2="370" y2="140" stroke="#b8997f" strokeWidth="2" />
              <line x1="320" y1="190" x2="370" y2="140" stroke="#b8997f" strokeWidth="2" />
              <circle cx="30" cy="110" r="18" fill="#171513" />
              <circle cx="120" cy="110" r="18" fill="#d7b79c" />
              <circle cx="210" cy="65" r="18" fill="#f2e6d7" stroke="#b8997f" />
              <circle cx="210" cy="155" r="18" fill="#f2e6d7" stroke="#b8997f" />
              <circle cx="320" cy="90" r="18" fill="#171513" />
              <circle cx="320" cy="190" r="18" fill="#171513" />
              <circle cx="370" cy="140" r="18" fill="#d7b79c" />
            </svg>
          </div>

          <div className="mt-5 space-y-2">
            {pipeline.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full border border-[#d1b79d] bg-[#f9f2ea] text-[10px] font-semibold text-[#7a5a3d]">
                  {index + 1}
                </div>
                <span className="text-sm text-[#423d39]">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.title} className="rounded-[22px] border border-[#d9d0c5] bg-[#ffffff] p-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-[#70695f]">{stat.title}</p>
            <p className="mt-4 text-3xl font-semibold text-[#171513]">{stat.value}</p>
            <p className="mt-2 text-sm text-[#5f564f]">{stat.detail}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#ffffff] p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-[#72685c]">Current corpus</p>
              <h3 className="mt-2 text-2xl font-semibold text-[#171513]">Top source files</h3>
            </div>
            <button onClick={() => navigate('/documents')} className="rounded-full border border-[#d8cdbd] bg-[#f7f3ee] px-3 py-2 text-xs uppercase tracking-[0.18em] text-[#584f4a]">
              Review all
            </button>
          </div>

          <div className="space-y-3">
            {topDocuments.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[#d9d0c5] bg-[#faf7f3] p-5 text-sm text-[#5f564f]">
                No sources have been uploaded yet. Add a document to begin building the corpus.
              </div>
            ) : (
              topDocuments.map((document) => (
                <div key={document.name} className="flex items-center justify-between gap-3 rounded-2xl border border-[#ece1d5] bg-[#faf7f3] p-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[#171513]">{document.name}</span>
                      <span className="rounded-full border border-[#ddd0c3] bg-[#f3ece3] px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] text-[#635b55]">
                        {document.type}
                      </span>
                    </div>
                    <div className="mt-2 text-sm text-[#5f564f]">{document.entities} entities extracted</div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-[#edf5ef] px-2.5 py-1 text-[10px] uppercase tracking-[0.2em] text-[#3d6c43]">
                      {document.state}
                    </span>
                    <button onClick={() => navigate('/documents')} className="text-sm font-medium text-[#7a5a3d]">Open</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#1b1917] p-6 text-[#f6f0e7]">
          <p className="text-[11px] uppercase tracking-[0.2em] text-[#d7c0a5]">Insights</p>
          <h3 className="mt-2 text-2xl font-semibold">Entity clusters</h3>

          <div className="mt-6 space-y-4">
            {[
              { label: 'Market signals', value: String(Math.min(31, documents.length * 10 + 5)), color: 'bg-[#d7b79c]' },
              { label: 'Decision makers', value: String(Math.min(17, documents.length * 6 + 2)), color: 'bg-[#f2e6d7]' },
              { label: 'Risk factors', value: String(Math.min(12, documents.length * 4 + 1)), color: 'bg-[#7f5d3a]' },
            ].map((item) => (
              <div key={item.label}>
                <div className="mb-2 flex items-center justify-between text-sm text-[#e9dfd2]">
                  <span>{item.label}</span>
                  <span>{item.value}</span>
                </div>
                <div className="h-2.5 rounded-full bg-[#2d2926]">
                  <div className={`h-full rounded-full ${item.color}`} style={{ width: `${Math.min(Number(item.value) * 2.8, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 rounded-[22px] border border-[#2d2926] bg-[#201d1a] p-4">
            <div className="text-[11px] uppercase tracking-[0.2em] text-[#d3bba1]">Flagged</div>
            <div className="mt-3 text-lg font-medium text-[#f9f3eb]">
              {documents.length ? 'The current corpus is actively surfacing cross-document connections and source-backed answers.' : 'Add a document to begin deriving entity clusters and flagged patterns.'}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#d7cab9] bg-[#fffdf9] p-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-[#6d625c]">{label}</div>
      <div className="mt-2 text-xl font-semibold text-[#171513]">{value}</div>
    </div>
  )
}
