import { useCallback, useState } from 'react'
import { compressForUpload } from '../utils/imageCompressor'
import { useAppStore } from '../stores/appStore'

export function useImageUpload() {
  const setOriginalFile = useAppStore((s) => s.setOriginalFile)
  const setCompressedFile = useAppStore((s) => s.setCompressedFile)

  const [compressing, setCompressing] = useState(false)
  const [compressError, setCompressError] = useState<string | null>(null)

  const acceptFile = useCallback(
    async (file: File) => {
      setCompressError(null)
      const previewUrl = URL.createObjectURL(file)
      setOriginalFile(file, previewUrl)

      setCompressing(true)
      try {
        const compressed = await compressForUpload(file)
        setCompressedFile(compressed)
      } catch (e: any) {
        setCompressError(e?.message || 'Failed to compress image')
        setCompressedFile(null)
      } finally {
        setCompressing(false)
      }
    },
    [setOriginalFile, setCompressedFile]
  )

  return { acceptFile, compressing, compressError }
}
