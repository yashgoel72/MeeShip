import { create } from 'zustand'

type Screen = 'landing' | 'processing' | 'result'

export type OptimizeResult = {
  id: string
  blob_url: string | null
  original_blob_url: string | null
  variant_blob_urls?: string[] | null
  original_filename?: string
  status?: 'success' | 'error'
  error_message?: string | null
  metrics?: {
    input_size_bytes?: number
    output_size_bytes?: number
    processing_time_ms?: number
    size_reduction_percent?: number
  }
  cost?: {
    savings_percentage?: number
    shipping_cost_inr?: number
  }
}

type ProcessingStep = {
  key: 'detect' | 'optimize' | 'background' | 'compress'
  label: string
  status: 'pending' | 'active' | 'done'
}

type AppState = {
  screen: Screen

  originalFile: File | null
  compressedFile: File | null
  originalPreviewUrl: string | null

  isSubmitting: boolean
  steps: ProcessingStep[]

  result: OptimizeResult | null
  optimizedPreviewUrl: string | null

  downloadState: 'idle' | 'downloading' | 'saved'
  error: string | null

  setScreen: (screen: Screen) => void
  setOriginalFile: (file: File | null, previewUrl: string | null) => void
  setCompressedFile: (file: File | null) => void
  resetFlow: () => void
  startProcessing: () => void
  markStep: (key: ProcessingStep['key'], status: ProcessingStep['status']) => void
  setResult: (result: OptimizeResult | null) => void
  setOptimizedPreviewUrl: (url: string | null) => void
  setError: (error: string | null) => void
  setDownloadState: (state: AppState['downloadState']) => void
}

const initialSteps: ProcessingStep[] = [
  { key: 'detect', label: 'Analyzing your product...', status: 'pending' },
  { key: 'optimize', label: 'Reducing shipping weight...', status: 'pending' },
  { key: 'background', label: 'Making it Meesho-ready...', status: 'pending' },
  { key: 'compress', label: 'Finalizing for lowest slab...', status: 'pending' },
]

export const useAppStore = create<AppState>((set, get) => ({
  screen: 'landing',

  originalFile: null,
  compressedFile: null,
  originalPreviewUrl: null,

  isSubmitting: false,
  steps: initialSteps,

  result: null,
  optimizedPreviewUrl: null,

  downloadState: 'idle',
  error: null,

  setScreen: (screen) => set({ screen }),

  setOriginalFile: (file, previewUrl) => {
    const prev = get().originalPreviewUrl
    if (prev && prev.startsWith('blob:')) URL.revokeObjectURL(prev)
    set({
      originalFile: file,
      originalPreviewUrl: previewUrl,
      compressedFile: null,
      result: null,
      optimizedPreviewUrl: null,
      error: null,
      downloadState: 'idle',
    })
  },

  setCompressedFile: (file) => set({ compressedFile: file }),

  resetFlow: () => {
    const prev = get().originalPreviewUrl
    if (prev && prev.startsWith('blob:')) URL.revokeObjectURL(prev)
    set({
      screen: 'landing',
      originalFile: null,
      compressedFile: null,
      originalPreviewUrl: null,
      isSubmitting: false,
      steps: initialSteps,
      result: null,
      optimizedPreviewUrl: null,
      downloadState: 'idle',
      error: null,
    })
  },

  startProcessing: () =>
    set({
      screen: 'processing',
      isSubmitting: true,
      steps: initialSteps.map((s, idx) => (idx === 0 ? { ...s, status: 'active' } : s)),
      error: null,
      downloadState: 'idle',
    }),

  markStep: (key, status) =>
    set({
      steps: get().steps.map((s) => (s.key === key ? { ...s, status } : s)),
    }),

  setResult: (result) => set({ result }),

  setOptimizedPreviewUrl: (url) => set({ optimizedPreviewUrl: url }),

  setError: (error) => set({ error, isSubmitting: false }),

  setDownloadState: (state) => set({ downloadState: state }),
}))
