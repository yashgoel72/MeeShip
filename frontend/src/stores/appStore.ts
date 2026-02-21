import { create } from 'zustand'

type Screen = 'landing' | 'processing' | 'result'

export type VariantMeta = {
  url: string
  tile_index: number
  variant_index: number
  variant_type: string
  tile_name: string
  variant_label: string
  shipping_cost?: {
    shipping_charges: number
    transfer_price: number
    selling_price: number
    duplicate_pid?: number | null
  }
  shipping_error?: {
    error_code: 'SESSION_EXPIRED' | 'NOT_LINKED' | string
    message: string
  }
}

export type OptimizeResult = {
  id: string
  blob_url: string | null
  original_blob_url: string | null
  variant_blob_urls?: string[] | null
  variants?: VariantMeta[] | null  // Detailed variant info for streaming
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

export type StreamingProgress = {
  stage: 'idle' | 'generating' | 'processing' | 'uploading' | 'complete' | 'error'
  progress: number  // 0-100
  message: string
  completed: number  // Variants completed
  total: number      // Total expected variants (30)
  errors: string[]   // Error messages collected during streaming
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

  // Streaming state
  streamingProgress: StreamingProgress

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

  // Streaming actions
  setStreamingProgress: (progress: Partial<StreamingProgress>) => void
  addVariant: (variant: VariantMeta) => void
  addStreamingError: (error: string) => void
  resetStreaming: () => void
}

const initialSteps: ProcessingStep[] = [
  { key: 'detect', label: 'Analyzing your product...', status: 'pending' },
  { key: 'optimize', label: 'Reducing shipping weight...', status: 'pending' },
  { key: 'background', label: 'Making it Meesho-ready...', status: 'pending' },
  { key: 'compress', label: 'Finalizing for lowest slab...', status: 'pending' },
]

const initialStreamingProgress: StreamingProgress = {
  stage: 'idle',
  progress: 0,
  message: '',
  completed: 0,
  total: 30,
  errors: [],
}

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

  streamingProgress: initialStreamingProgress,

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
      streamingProgress: initialStreamingProgress,
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
      streamingProgress: initialStreamingProgress,
    })
  },

  startProcessing: () =>
    set({
      screen: 'processing',
      isSubmitting: true,
      steps: initialSteps.map((s, idx) => (idx === 0 ? { ...s, status: 'active' } : s)),
      error: null,
      downloadState: 'idle',
      streamingProgress: {
        ...initialStreamingProgress,
        stage: 'generating',
        message: 'Starting optimization...',
      },
    }),

  markStep: (key, status) =>
    set({
      steps: get().steps.map((s) => (s.key === key ? { ...s, status } : s)),
    }),

  setResult: (result) => set({ result }),

  setOptimizedPreviewUrl: (url) => set({ optimizedPreviewUrl: url }),

  setError: (error) => set({ error, isSubmitting: false }),

  setDownloadState: (state) => set({ downloadState: state }),

  // === Streaming actions ===

  setStreamingProgress: (progress) =>
    set({
      streamingProgress: { ...get().streamingProgress, ...progress },
    }),

  addVariant: (variant) => {
    const current = get().result
    const currentVariants = current?.variants || []
    const currentUrls = current?.variant_blob_urls || []
    
    set({
      result: {
        ...current,
        id: current?.id || '',
        blob_url: current?.blob_url || null,
        original_blob_url: current?.original_blob_url || null,
        variants: [...currentVariants, variant],
        variant_blob_urls: [...currentUrls, variant.url],
      },
      streamingProgress: {
        ...get().streamingProgress,
        completed: currentVariants.length + 1,
      },
    })
  },

  addStreamingError: (error) =>
    set({
      streamingProgress: {
        ...get().streamingProgress,
        errors: [...get().streamingProgress.errors, error],
      },
    }),

  resetStreaming: () =>
    set({
      streamingProgress: initialStreamingProgress,
    }),
}))
