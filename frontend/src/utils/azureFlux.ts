import { uploadImage } from '../services/api'
import type { OptimizeResult } from '../stores/appStore'

export async function generateOptimizedImage(file: File): Promise<OptimizeResult> {
  const form = new FormData()
  // Backend expects field name: "file"
  form.append('file', file)

  const res = await uploadImage(form)
  return res.data as OptimizeResult
}
