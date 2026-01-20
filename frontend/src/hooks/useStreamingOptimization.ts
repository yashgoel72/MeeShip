import { useCallback, useRef } from 'react'
import { useAppStore } from '../stores/appStore'
import { streamOptimization, StreamingVariant, StreamingStatus, StreamingError, StreamingComplete } from '../services/api'
import { compressForUpload } from '../utils/imageCompressor'
import { trackEvent } from '../utils/posthog'
import { useAuth } from '../context/AuthContext'

/**
 * Hook for streaming image optimization with real-time variant delivery.
 * Variants appear in the UI as they're generated and uploaded.
 */
export function useStreamingOptimization() {
  const { refreshCredits } = useAuth()
  const setScreen = useAppStore((s) => s.setScreen)
  const startProcessing = useAppStore((s) => s.startProcessing)
  const setResult = useAppStore((s) => s.setResult)
  const setError = useAppStore((s) => s.setError)
  const setStreamingProgress = useAppStore((s) => s.setStreamingProgress)
  const addVariant = useAppStore((s) => s.addVariant)
  const addStreamingError = useAppStore((s) => s.addStreamingError)
  const markStep = useAppStore((s) => s.markStep)

  const abortRef = useRef<(() => void) | null>(null)

  const startStreaming = useCallback(
    async (file: File) => {
      // Start the processing UI
      startProcessing()
      trackEvent('optimize_stream_start')

      try {
        // Compress the image first
        const compressed = await compressForUpload(file)
        const fileToUpload = compressed || file

        // Prepare form data
        const formData = new FormData()
        formData.append('file', fileToUpload, file.name)

        // Initialize result state
        setResult({
          id: '',
          blob_url: null,
          original_blob_url: null,
          variant_blob_urls: [],
          variants: [],
          status: 'success',
        })

        // Start streaming
        const { abort } = streamOptimization(formData, {
          onStatus: (status: StreamingStatus) => {
            setStreamingProgress({
              stage: status.stage,
              progress: status.progress,
              message: status.message,
            })

            // Update processing steps based on stage
            if (status.stage === 'generating') {
              markStep('detect', 'done')
              markStep('optimize', 'active')
            } else if (status.stage === 'processing') {
              markStep('optimize', 'done')
              markStep('background', 'active')
            } else if (status.stage === 'uploading') {
              markStep('background', 'done')
              markStep('compress', 'active')
            }
          },

          onVariant: (variant: StreamingVariant) => {
            addVariant({
              url: variant.url,
              tile_index: variant.tile_index,
              variant_index: variant.variant_index,
              variant_type: variant.variant_type,
              tile_name: variant.tile_name,
              variant_label: variant.variant_label,
            })

            setStreamingProgress({
              progress: variant.progress,
              completed: variant.completed,
              total: variant.total,
              message: `Generated ${variant.completed}/${variant.total} variants...`,
            })

            // Switch to result screen once we have some variants
            if (variant.completed === 1) {
              setScreen('result')
            }
          },

          onError: (error: StreamingError) => {
            if (error.recoverable) {
              // Non-fatal error, just log it
              addStreamingError(error.message)
              console.warn('Recoverable streaming error:', error.message)
            } else {
              // Fatal error, stop processing
              setError(error.message)
              setStreamingProgress({
                stage: 'error',
                message: error.message,
              })
              trackEvent('optimize_stream_error', { error: error.message })
            }
          },

          onComplete: (result: StreamingComplete) => {
            markStep('compress', 'done')
            
            setStreamingProgress({
              stage: 'complete',
              progress: 100,
              completed: result.successful,
              total: result.total,
              message: `Complete! ${result.successful}/${result.total} variants ready.`,
            })

            // Update result with final data
            setResult({
              id: result.id,
              blob_url: result.grid_url,
              original_blob_url: result.original_url,
              variant_blob_urls: result.variant_urls,
              status: 'success',
              metrics: result.metrics,
            })

            // Refresh credits after successful optimization (credit was consumed)
            refreshCredits()

            setScreen('result')
            trackEvent('optimize_stream_complete', {
              successful: result.successful,
              failed: result.failed,
              processing_time_ms: result.processing_time_ms,
            })
          },
        })

        abortRef.current = abort
      } catch (e: any) {
        setError(e?.message || 'Streaming optimization failed')
        trackEvent('optimize_stream_error', { error: e?.message })
      }
    },
    [startProcessing, setResult, setError, setStreamingProgress, addVariant, addStreamingError, markStep, setScreen, refreshCredits]
  )

  const cancelStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current()
      abortRef.current = null
      setError('Optimization cancelled')
      trackEvent('optimize_stream_cancelled')
    }
  }, [setError])

  return { startStreaming, cancelStreaming }
}
