import { useEffect, useState } from 'react'

interface DocumentItem {
  id: string
  filename: string
  status: string
  file_size_bytes: number
  character_count: number
  created_at: string
}

interface DocumentListResponse {
  items: DocumentItem[]
  total: number
}

const formatBytes = (bytes: number) => `${(bytes / 1024).toFixed(1)} KB`

export default function Documents() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState('')

  const loadDocuments = async () => {
    const response = await fetch('/api/documents/?limit=100')
    if (!response.ok) throw new Error('Unable to load documents')
    const data: DocumentListResponse = await response.json()
    setDocuments(data.items)
  }

  useEffect(() => {
    loadDocuments()
      .catch((loadError: Error) => setError(loadError.message))
      .finally(() => setIsLoading(false))
  }, [])

  const uploadDocument = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Upload failed')
      }
      setSelectedFile(null)
      const fileInput = document.getElementById('document-file') as HTMLInputElement | null
      if (fileInput) fileInput.value = ''
      await loadDocuments()
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const removeDocument = async (documentId: string) => {
    setError('')
    const response = await fetch(`/api/documents/${documentId}`, { method: 'DELETE' })
    if (!response.ok) {
      setError('Unable to delete document')
      return
    }
    setDocuments((current) => current.filter((document) => document.id !== documentId))
  }

  return (
    <div className="mx-auto max-w-6xl animate-[fadeIn_420ms_ease-out]">
      <div className="mb-6 rounded-2xl border border-[#b9ddd5] bg-[#e1f1ed] p-6 shadow-[0_18px_50px_rgba(22,124,120,0.08)]">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#167c78]">Ingestion desk</p>
        <h2 className="mb-1 font-serif text-2xl font-semibold text-[#17212b]">Bring a document into focus</h2>
        <p className="mb-5 text-sm text-[#4f665f]">Upload PDF, DOCX, or TXT files for extraction.</p>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            id="document-file"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
            className="block w-full text-sm text-[#4f665f] file:mr-4 file:rounded-md file:border-0 file:bg-[#17212b] file:px-4 file:py-2 file:text-sm file:font-medium file:text-white"
          />
          <button
            type="button"
            onClick={uploadDocument}
            disabled={!selectedFile || isUploading}
            className="rounded-md bg-[#f47f68] px-4 py-2 text-sm font-semibold text-[#17212b] shadow-sm disabled:cursor-not-allowed disabled:bg-white/60"
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      <div className="overflow-hidden rounded-2xl border border-[#dfe6df] bg-white/85 shadow-[0_18px_50px_rgba(23,33,43,0.05)]">
        <div className="border-b border-[#e6ebe6] px-6 py-5">
          <h2 className="font-serif text-2xl font-semibold text-[#17212b]">Documents <span className="font-sans text-sm font-normal text-[#718078]">({documents.length})</span></h2>
        </div>
        {isLoading ? (
          <p className="p-6 text-sm text-[#718078]">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="p-6 text-sm text-[#718078]">No documents uploaded yet.</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {documents.map((document) => (
              <div key={document.id} className="flex flex-col gap-3 px-6 py-5 transition-colors hover:bg-[#f4f8f5] sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-medium text-[#17212b]">{document.filename}</p>
                  <p className="text-sm text-[#718078]">
                    {formatBytes(document.file_size_bytes)} · {document.character_count.toLocaleString()} characters
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="rounded-full bg-[#e1f1ed] px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#167c78]">{document.status}</span>
                  <button type="button" onClick={() => removeDocument(document.id)} className="text-sm font-semibold text-[#d45e50] hover:text-[#a53e35]">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
