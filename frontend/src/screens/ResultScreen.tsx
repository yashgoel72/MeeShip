import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import PaymentModal from '../components/PaymentModal'
import { useAppStore } from '../stores/appStore'
import { proxyMinioUrl } from '../utils/minioProxy.ts'
import { trackEvent } from '../utils/posthog.ts'
import { useAuth } from '../context/AuthContext'

function ConfettiBurst() {
  const pieces = Array.from({ length: 18 }).map((_, i) => i)
  return (
    <div className="pointer-events-none fixed inset-x-0 top-16 z-40 flex justify-center">
      <div className="relative h-0 w-0">
        {pieces.map((i) => (
          <motion.div
            key={i}
            className="absolute h-2 w-2 rounded-sm bg-success"
            initial={{ opacity: 0, x: 0, y: 0, rotate: 0 }}
            animate={{
              opacity: [0, 1, 0],
              x: (i - 9) * 10,
              y: 120 + (i % 3) * 18,
              rotate: 180 + i * 10,
            }}
            transition={{ duration: 0.9, ease: 'easeOut' }}
          />
        ))}
      </div>
    </div>
  )
}

export default function ResultScreen() {
  const resetFlow = useAppStore((s) => s.resetFlow)
  const result = useAppStore((s) => s.result)
  const downloadState = useAppStore((s) => s.downloadState)
  const setDownloadState = useAppStore((s) => s.setDownloadState)
  const { user, isAuthenticated } = useAuth()

  const [confetti, setConfetti] = useState(true)
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [downloadingAll, setDownloadingAll] = useState(false)

  const variantUrls = useMemo(() => {
    const urls = result?.variant_blob_urls
    if (!urls || urls.length === 0) return []
    return urls.slice(0, 6).map((u) => proxyMinioUrl(u))
  }, [result?.variant_blob_urls])

  if (!result || variantUrls.length === 0) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16">
        <div className="rounded-3xl bg-white p-6 ring-1 ring-slate-200">
          <div className="text-lg font-semibold text-slate-900">No variants yet</div>
            <div className="mt-1 text-sm text-slate-600">No images generated yet. Please try generating again to get 6 variants.</div>
          <button
            type="button"
            onClick={resetFlow}
            className="mt-4 rounded-2xl bg-meesho px-4 py-3 text-sm font-semibold text-white hover:bg-meesho/90"
          >
            ← Back
          </button>
        </div>
      </div>
    )
  }

  const download = async (url: string, filename: string) => {
    try {
      setDownloadState('downloading')
      trackEvent('download_clicked')

      const res = await fetch(url)
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      setDownloadState('saved')
      window.setTimeout(() => setDownloadState('idle'), 2500)
      trackEvent('download_success')
    } catch {
      setDownloadState('idle')
    }
  }

  const downloadAll = async () => {
    setDownloadingAll(true)
    trackEvent('download_all_clicked')
    for (let i = 0; i < variantUrls.length; i++) {
      await download(variantUrls[i], `meeship_variant_${i + 1}.jpg`)
      // Small delay between downloads
      await new Promise((r) => setTimeout(r, 300))
    }
    setDownloadingAll(false)
    trackEvent('download_all_success')
  }

  return (
    <div className="min-h-screen bg-offwhite">
      {confetti && <ConfettiBurst />}
      <PaymentModal open={paymentOpen} onClose={() => setPaymentOpen(false)} />

      <div className="mx-auto max-w-5xl px-4 pt-8">
        <button
          type="button"
          onClick={() => {
            trackEvent('generate_another')
            resetFlow()
          }}
          className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-white"
        >
          ← Generate Another
        </button>

        <motion.div
          className="mt-5 text-3xl font-extrabold text-slate-900"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          onAnimationComplete={() => setConfetti(false)}
        >
          Your 6 shipping-optimized images are ready!
        </motion.div>
      </div>

      <div className="mx-auto w-full max-w-5xl px-4 pb-32">
        <div className="mt-6 rounded-3xl bg-white p-6 ring-1 ring-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-bold text-slate-900">6 Variants Ready</div>
              <div className="mt-1 text-sm text-slate-500">Each variant is optimized for Meesho listings — pick your favorites!</div>
            </div>
            <button
              type="button"
              onClick={downloadAll}
              disabled={downloadingAll || downloadState === 'downloading'}
              className="hidden sm:flex items-center gap-2 rounded-xl bg-meesho px-4 py-2.5 text-sm font-semibold text-white hover:bg-meesho/90 transition-colors disabled:opacity-60"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {downloadingAll ? 'Downloading...' : 'Download All'}
            </button>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4">
            {variantUrls.map((u, idx) => (
              <motion.div
                key={u}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group relative aspect-square overflow-hidden rounded-2xl bg-slate-50 ring-1 ring-slate-200 hover:ring-meesho hover:ring-2 transition-all"
              >
                <img src={u} alt={`Variant ${idx + 1}`} className="h-full w-full object-cover" />
                {/* Variant number badge */}
                <div className="absolute top-2 left-2 rounded-lg bg-black/60 px-2 py-1 text-xs font-semibold text-white backdrop-blur-sm">
                  #{idx + 1}
                </div>
                {/* Hover overlay with download */}
                <div className="absolute inset-0 flex items-center justify-center bg-black/0 opacity-0 group-hover:bg-black/30 group-hover:opacity-100 transition-all">
                  <button
                    type="button"
                    onClick={() => download(u, `meeship_variant_${idx + 1}.jpg`)}
                    disabled={downloadState === 'downloading'}
                    className="flex items-center gap-1.5 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-900 shadow-lg hover:bg-slate-50 transition-colors disabled:opacity-60"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download
                  </button>
                </div>
                {/* Mobile download button (always visible) */}
                <button
                  type="button"
                  onClick={() => download(u, `meeship_variant_${idx + 1}.jpg`)}
                  disabled={downloadState === 'downloading'}
                  className="absolute bottom-2 right-2 sm:hidden rounded-full bg-white/95 p-2 shadow-lg disabled:opacity-60"
                >
                  <svg className="h-4 w-4 text-meesho" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
              </motion.div>
            ))}
          </div>

          {/* Mobile download all button */}
          <button
            type="button"
            onClick={downloadAll}
            disabled={downloadingAll || downloadState === 'downloading'}
            className="mt-4 w-full sm:hidden flex items-center justify-center gap-2 rounded-xl bg-meesho px-4 py-3 text-sm font-semibold text-white hover:bg-meesho/90 transition-colors disabled:opacity-60"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {downloadingAll ? 'Downloading...' : 'Download All 6 Variants'}
          </button>
        </div>

        {/* Tips section */}
        <div className="mt-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 p-4 ring-1 ring-emerald-100">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-emerald-100 p-2">
              <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <div className="text-sm font-semibold text-emerald-800">Pro tip</div>
              <div className="text-sm text-emerald-700">Use Variant #1 as your main listing image for best results. Try different variants if one doesn't perform well!</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom bar - Credit status or upgrade prompt */}
      <div className="fixed bottom-0 inset-x-0 bg-gradient-to-t from-white via-white to-transparent pt-6 pb-5">
        <div className="mx-auto max-w-5xl px-4">
          {isAuthenticated && user && (user.credits ?? 0) > 0 ? (
            // Paid user - show credit balance
            <div className="rounded-2xl bg-gradient-to-r from-slate-800 to-slate-700 p-4 text-white shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-white/20 p-2">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-lg font-bold">{user.credits} credits remaining</div>
                    <div className="text-sm text-white/70">1 credit = 1 image generation</div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setPaymentOpen(true)}
                  className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 hover:bg-white/90 transition-colors"
                >
                  Buy More
                </button>
              </div>
            </div>
          ) : (
            // Trial/no credits - show upgrade prompt
            <div className="rounded-2xl bg-gradient-to-r from-meesho to-meesho/80 p-4 text-white shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg font-bold">Get more credits</div>
                  <div className="text-sm text-white/80">Starting at ₹99 for 10 images</div>
                </div>
                <button
                  type="button"
                  onClick={() => setPaymentOpen(true)}
                  className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-meesho hover:bg-white/90 transition-colors"
                >
                  Buy Credits
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
