/**
 * API client and service layer for the Multi-AI Knowledge Mining backend.
 * Connects frontend React components to FastAPI endpoints via reverse proxy (/api).
 */

import axios from 'axios'

// Base axios instance. Vite proxy routes '/api' to backend (http://localhost:8000)
export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface DocumentMetadata {
  filename: string
  file_type: string
  file_size_bytes: number
  page_count: number | null
  character_count: number
  upload_timestamp: string
}

export interface DocumentItem {
  id: string
  filename: string
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | string
  file_size_bytes: number
  character_count: number
  upload_timestamp: string
  created_at: string
}

export interface DocumentDetail {
  id: string
  status: string
  metadata: DocumentMetadata
  raw_text: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  status: string
  file_size_bytes: number
  message: string
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
  limit: number
  offset: number
}

export interface DocumentStats {
  total_documents: number
  api_version: string
}

export interface ChunkMetadata {
  document_id: string
  start_position: number
  end_position: number
  section: string | null
  paragraph_index: number | null
  sentence_count: number
  quality_score: number
  quality_level: 'low' | 'medium' | 'high'
  language: string | null
  is_normalized: boolean
  token_count: number | null
  chunking_strategy: string
}

export interface ChunkItem {
  id: string
  document_id: string
  text: string
  metadata: ChunkMetadata
  created_at: string
}

export interface ChunkListResponse {
  chunks: ChunkItem[]
  total_count: number
  page: number
  page_size: number
}

export interface ChunkDocumentRequest {
  strategy?: 'fixed_size' | 'semantic_sentence' | 'sliding_window'
  chunk_size?: number
  overlap?: number
  detect_language?: boolean
}

// ── Document API Service ────────────────────────────────────────

export const documentApi = {
  /**
   * Upload a document file (PDF, DOCX, TXT) via multipart/form-data.
   */
  async upload(file: File, onProgress?: (percent: number) => void): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<DocumentUploadResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    })
    return response.data
  },

  /**
   * List all uploaded documents with pagination.
   */
  async list(limit = 50, offset = 0): Promise<DocumentListResponse> {
    const response = await apiClient.get<DocumentListResponse>('/documents/', {
      params: { limit, offset },
    })
    return response.data
  },

  /**
   * Get complete details of a document including extracted raw text.
   */
  async get(id: string): Promise<DocumentDetail> {
    const response = await apiClient.get<DocumentDetail>(`/documents/${id}`)
    return response.data
  },

  /**
   * Get document status and stats.
   */
  async getStatus(id: string) {
    const response = await apiClient.get(`/documents/${id}/status`)
    return response.data
  },

  /**
   * Delete a document by ID.
   */
  async delete(id: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/documents/${id}`)
    return response.data
  },

  /**
   * Get document summary statistics.
   */
  async getStats(): Promise<DocumentStats> {
    const response = await apiClient.get<DocumentStats>('/documents/stats/summary')
    return response.data
  },
}

// ── Chunk API Service ──────────────────────────────────────────

export const chunkApi = {
  /**
   * Trigger text chunking on an uploaded document.
   */
  async chunkDocument(documentId: string, params: ChunkDocumentRequest = {}): Promise<ChunkListResponse> {
    const response = await apiClient.post<ChunkListResponse>(
      `/chunks/document/${documentId}/chunk`,
      {
        document_id: documentId,
        strategy: params.strategy || 'fixed_size',
        chunk_size: params.chunk_size || 512,
        overlap: params.overlap || 50,
        detect_language: params.detect_language !== false,
      }
    )
    return response.data
  },

  /**
   * List chunks for a specific document.
   */
  async getDocumentChunks(documentId: string, limit = 50, offset = 0): Promise<ChunkListResponse> {
    const response = await apiClient.get<ChunkListResponse>(`/chunks/document/${documentId}`, {
      params: { limit, offset },
    })
    return response.data
  },

  /**
   * Search chunks by text substring and metadata filters.
   */
  async search(query: string, documentId?: string, limit = 20) {
    const response = await apiClient.post('/chunks/search', {
      query,
      document_id: documentId,
      limit,
    })
    return response.data
  },
}
