import ProcessingOverlay from '../components/ProcessingOverlay'
import { useAppStore } from '../stores/appStore'

export default function ProcessingScreen() {
  const originalUrl = useAppStore((s) => s.originalPreviewUrl)
  const optimizedUrl = useAppStore((s) => s.optimizedPreviewUrl)

  return <ProcessingOverlay originalUrl={originalUrl} optimizedUrl={optimizedUrl} />
}
