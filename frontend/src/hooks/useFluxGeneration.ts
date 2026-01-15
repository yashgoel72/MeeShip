import { useCallback } from 'react'
import { useAppStore } from '../stores/appStore'
import { generateOptimizedImage } from '../utils/azureFlux'
import { proxyMinioUrl } from '../utils/minioProxy'
import { useAuth } from '../context/AuthContext'

export function useFluxGeneration() {
  const { refreshCredits } = useAuth()
  const compressedFile = useAppStore((s) => s.compressedFile)
  const startProcessing = useAppStore((s) => s.startProcessing)
  const markStep = useAppStore((s) => s.markStep)
  const setResult = useAppStore((s) => s.setResult)
  const setOptimizedPreviewUrl = useAppStore((s) => s.setOptimizedPreviewUrl)
  const setError = useAppStore((s) => s.setError)
  const setScreen = useAppStore((s) => s.setScreen)

  const run = useCallback(async () => {
    if (!compressedFile) {
      setError('Please upload an image first.')
      return
    }

    startProcessing()

    // Simple staged progression (timed), then we reconcile with actual request timing.
    markStep('detect', 'active')

    const t1 = window.setTimeout(() => {
      markStep('detect', 'done')
      markStep('optimize', 'active')
    }, 450)

    const t2 = window.setTimeout(() => {
      markStep('optimize', 'done')
      markStep('background', 'active')
    }, 1200)

    const t3 = window.setTimeout(() => {
      markStep('background', 'done')
      markStep('compress', 'active')
    }, 2000)

    try {
      const res = await generateOptimizedImage(compressedFile)
      setResult(res)

      if (res.blob_url) {
        setOptimizedPreviewUrl(proxyMinioUrl(res.blob_url))
      }

      // Refresh credits after successful generation
      await refreshCredits()

      markStep('compress', 'done')
      setScreen('result')
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Optimization failed')
      setScreen('landing')
    } finally {
      window.clearTimeout(t1)
      window.clearTimeout(t2)
      window.clearTimeout(t3)
    }
  }, [compressedFile, markStep, setError, setOptimizedPreviewUrl, setResult, setScreen, startProcessing])

  return { run }
}
