import { useRef, useState } from 'react'
import { useKnowledge } from '../context/KnowledgeContext'

const statusStyles: Record<string, string> = {
  completed: 'bg-[#edf5ef] text-[#406d42]',
  processing: 'bg-[#f8efe8] text-[#8a5b32]',
  uploaded: 'bg-[#f3f0ee] text-[#625b55]',
  failed: 'bg-[#f9e7e5] text-[#9a4941]',
}

export default function Documents() {
  const { documents, selectedDocument, setSelectedDocumentId, uploadDocument, deleteDocument, refreshDocuments, loadDocumentDetails } = useKnowledge()
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState('')
  const [detailText, setDetailText] = useState('')

  const openDocument = async (id: string) => {
    setSelectedDocumentId(id)
    const detail = await loadDocumentDetails(id)
    setDetailText(detail?.rawText ?? 'No extracted content available yet.')
  }

  const handleUploadClick = () => inputRef.current?.click()

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError('')
    setIsUploading(true)

    try {
      await uploadDocument(file)
      const nextDocument = documents[0]
      if (nextDocument) {
        await openDocument(nextDocument.id)
      }
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Upload failed')
    } finally {
      setIsUploading(false)
      event.target.value = ''
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this document and its extracted data from the workspace?')) return

    try {
      await deleteDocument(id)
      setDetailText('')
      await refreshDocuments()
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'Delete failed')
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[28px] border border-[#d9d0c5] bg-[#fffaf4] p-6 md:p-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#72685c]">Archive</p>
            <h2 className="editorial-display mt-2 text-4xl text-[#171513]">Document intake</h2>
          </div>

          <button onClick={handleUploadClick} className="rounded-full bg-[#171513] px-5 py-3 text-sm font-medium text-[#f7f3ee] transition hover:bg-[#2d2824]">
            {isUploading ? 'Uploading...' : 'Upload source'}
          </button>
          <input ref={inputRef} type="file" className="hidden" onChange={handleUpload} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#f2eadf] p-6">
          <h3 className="text-lg font-semibold text-[#171513]">Add a source</h3>
          <div className="mt-5 rounded-[24px] border border-dashed border-[#b8a894] bg-[#f8f3ed] p-8 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-[#d3b99d] bg-[#fffdf9] text-[#705a43]">
              +
            </div>
            <p className="mt-4 text-lg font-medium text-[#171513]">Drop files here</p>
            <p className="mt-2 text-sm text-[#5f564f]">PDF, DOCX, HTML, or TXT up to 50 MB</p>
            <button onClick={handleUploadClick} className="mt-5 rounded-full border border-[#d0c4b7] bg-white px-4 py-2 text-sm font-medium text-[#171513]">
              Browse files
            </button>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-[#e3d7c8] bg-[#fffdfb] p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-[#70695f]">Queued</div>
              <div className="mt-2 text-2xl font-semibold text-[#171513]">{documents.filter((document) => document.status !== 'completed').length}</div>
            </div>
            <div className="rounded-2xl border border-[#e3d7c8] bg-[#fffdfb] p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-[#70695f]">Avg. parse</div>
              <div className="mt-2 text-2xl font-semibold text-[#171513]">{documents.length ? '18 sec' : '—'}</div>
            </div>
          </div>

          {error ? <div className="mt-4 rounded-2xl border border-[#e2b3ae] bg-[#fff5f3] px-3 py-2 text-sm text-[#7d433f]">{error}</div> : null}
        </div>

        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#ffffff] p-6">
          <div className="mb-5 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-[#171513]">Recent uploads</h3>
            <span className="text-sm text-[#5f564f]">{documents.length} source{documents.length === 1 ? '' : 's'}</span>
          </div>

          <div className="space-y-3">
            {documents.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[#d9d0c5] bg-[#faf7f3] p-5 text-sm text-[#5f564f]">
                No sources are in the workspace yet.
              </div>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="flex flex-col gap-3 rounded-2xl border border-[#ece1d5] bg-[#faf7f3] p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="text-base font-medium text-[#171513]">{doc.filename}</div>
                    <div className="mt-1 text-sm text-[#5f564f]">{(doc.sizeBytes / 1024 / 1024).toFixed(1)} MB • Updated {new Date(doc.updatedAt).toLocaleDateString()}</div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className={`rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] ${statusStyles[doc.status]}`}>
                      {doc.status}
                    </span>
                    <button onClick={() => openDocument(doc.id)} className="text-sm font-medium text-[#7a5a3d]">Open</button>
                    <button onClick={() => handleDelete(doc.id)} className="text-sm font-medium text-[#8b4c45]">Delete</button>
                  </div>
                </div>
              ))
            )}
          </div>

          {selectedDocument ? (
            <div className="mt-6 rounded-[24px] border border-[#e5dcca] bg-[#faf7f3] p-4">
              <div className="mb-3 flex items-center justify-between">
                <h4 className="text-lg font-semibold text-[#171513]">{selectedDocument.filename}</h4>
                <span className="rounded-full bg-[#edf5ef] px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-[#406d42]">
                  {selectedDocument.status}
                </span>
              </div>
              <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-sm leading-6 text-[#4a433d]">{detailText || 'No extracted content has been loaded for this document yet.'}</pre>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
