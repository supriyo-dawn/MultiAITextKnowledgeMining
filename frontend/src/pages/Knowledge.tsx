import { useEffect, useState } from 'react'

export default function Knowledge() {
  const [available, setAvailable] = useState<boolean | null>(null)

  useEffect(() => {
    fetch('/api/knowledge/graph')
      .then((response) => response.json())
      .then((data) => setAvailable(data.available))
      .catch(() => setAvailable(false))
  }, [])

  return (
    <div className="mx-auto max-w-6xl animate-[fadeIn_420ms_ease-out]">
      <div className="rounded-2xl border border-[#dfe6df] bg-white/85 p-6 shadow-[0_18px_50px_rgba(23,33,43,0.05)]">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#167c78]">Graph desk</p>
        <h2 className="mb-2 font-serif text-2xl font-semibold text-[#17212b]">Knowledge graph</h2>
        <p className="text-sm text-[#718078]">{available === null ? 'Checking graph availability...' : available ? 'Local entities and relationships are available.' : 'Graph services are not configured yet.'}</p>
      </div>
    </div>
  )
}
