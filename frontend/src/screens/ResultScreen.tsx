import { useEffect, useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import PaymentModal from '../components/PaymentModal'
import ShippingCostBadge from '../components/ShippingCostBadge'
import SessionExpiredAlert from '../components/SessionExpiredAlert'
import MeeshoLinkModal from '../components/MeeshoLinkModal'
import { useAppStore, VariantMeta } from '../stores/appStore'
import { proxyMinioUrl } from '../utils/minioProxy.ts'

// Re-export store selectors used on this page
const useSscatName = () => useAppStore((s) => s.sscatName)
const useSscatBreadcrumb = () => useAppStore((s) => s.sscatBreadcrumb)
import { trackEvent } from '../utils/posthog.ts'
import { useAuth } from '../context/AuthContext'

// Tile names for grouping - 4 Shipping + 2 Lifestyle
const TILE_NAMES = [
  'Hero Front View',
  'Top View',
  '3/4 Angle',
  'Dark Luxury',
  'In-Use Lifestyle',
  'Styled Scene',
]

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

function ProgressBar({ progress, completed, total }: { progress: number; completed: number; total: number }) {
  return (
    <div className="rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 p-4 ring-1 ring-blue-100">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-blue-800">Generating variants...</div>
        <div className="text-sm font-medium text-blue-600">{completed}/{total} ready</div>
      </div>
      <div className="h-2 w-full rounded-full bg-blue-100 overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

export default function ResultScreen() {
  const resetFlow = useAppStore((s) => s.resetFlow)
  const result = useAppStore((s) => s.result)
  const streamingProgress = useAppStore((s) => s.streamingProgress)
  const downloadState = useAppStore((s) => s.downloadState)
  const setDownloadState = useAppStore((s) => s.setDownloadState)
  const sscatName = useSscatName()
  const sscatBreadcrumb = useSscatBreadcrumb()
  const { user, isAuthenticated } = useAuth()

  const [confetti, setConfetti] = useState(true)
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [downloadingAll, setDownloadingAll] = useState(false)
  const [showMeeshoModal, setShowMeeshoModal] = useState(false)
  const [meeshoRefreshKey, setMeeshoRefreshKey] = useState(0)

  // Warn user before leaving page (refresh/close) - results will be lost
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // Only warn if we have results
      if (result?.variants?.length || result?.variant_blob_urls?.length) {
        e.preventDefault()
        e.returnValue = 'Your generated images will be lost if you leave. Are you sure?'
        return e.returnValue
      }
    }
    
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [result])

  // Handler for "Generate Another" with confirmation
  const handleGenerateAnother = () => {
    const hasResults = result?.variants?.length || result?.variant_blob_urls?.length
    if (hasResults) {
      const confirmed = window.confirm(
        'Your current images will be lost. Make sure you\'ve downloaded the ones you need!\n\nAre you sure you want to generate new images?'
      )
      if (!confirmed) return
    }
    trackEvent('generate_another')
    resetFlow()
  }

  // Use detailed variants if available, otherwise fall back to flat URLs
  const variants: VariantMeta[] = useMemo(() => {
    if (result?.variants && result.variants.length > 0) {
      return result.variants.map((v) => ({
        ...v,
        url: proxyMinioUrl(v.url),
      }))
    }
    // Fallback: convert flat URLs to variant format (5 variants per tile)
    // All tiles get: Standard, Cool, Warm, Zoom Out, High Contrast
    const urls = result?.variant_blob_urls
    if (!urls || urls.length === 0) return []
    return urls.map((u, idx) => {
      const tileIdx = Math.floor(idx / 5)
      const variantIdx = idx % 5
      
      const variantTypes = ['standard', 'detail_focus', 'warm_minimal', 'hero_compact', 'high_contrast']
      const variantLabels = ['Standard', 'Cool Minimal', 'Warm Minimal', 'Zoom Out', 'High Contrast']
      
      return {
        url: proxyMinioUrl(u),
        tile_index: tileIdx,
        variant_index: variantIdx,
        variant_type: variantTypes[variantIdx],
        tile_name: TILE_NAMES[tileIdx] || `Tile ${tileIdx + 1}`,
        variant_label: variantLabels[variantIdx],
      } as VariantMeta
    })
  }, [result?.variants, result?.variant_blob_urls])

  // Stable random seeds per variant — assigned once, survives re-renders so
  // the order stays consistent as shipping costs stream in.
  const randSeeds = useRef<Map<string, number>>(new Map())

  // Compute shipping summary: all variants with shipping cost data (sorted by lowest)
  const shippingSummary = useMemo(() => {
    const withShipping = variants.filter((v) => v.shipping_cost != null)
    const hasSessionExpired = variants.some((v) => v.shipping_error?.error_code === 'SESSION_EXPIRED')
    if (withShipping.length === 0) return { hasData: false, hasSessionExpired, count: 0, totalChecked: variants.length, min: 0, max: 0, sellingPrice: 0, top10: [] as typeof variants }
    const charges = withShipping.map((v) => v.shipping_cost!.shipping_charges)
    // Assign a stable random seed to each variant (only once per key)
    for (const v of withShipping) {
      const key = `${v.tile_index}-${v.variant_index}`
      if (!randSeeds.current.has(key)) {
        randSeeds.current.set(key, Math.random())
      }
    }
    const sorted = [...withShipping].sort((a, b) => {
      const diff = a.shipping_cost!.shipping_charges - b.shipping_cost!.shipping_charges
      if (diff !== 0) return diff
      // Same cost → random tiebreaker so same-style images don't cluster
      return randSeeds.current.get(`${a.tile_index}-${a.variant_index}`)!
           - randSeeds.current.get(`${b.tile_index}-${b.variant_index}`)!
    })
    return {
      hasData: true,
      hasSessionExpired,
      count: withShipping.length,
      totalChecked: variants.length,
      min: Math.min(...charges),
      max: Math.max(...charges),
      sellingPrice: withShipping[0].shipping_cost!.selling_price,
      top10: sorted.slice(0, 10),
    }
  }, [variants])

  const isStreaming = streamingProgress.stage !== 'idle' && streamingProgress.stage !== 'complete' && streamingProgress.stage !== 'error'
  const totalExpected = streamingProgress.total || 30
  const completed = variants.length

  if (!result && !isStreaming) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16">
        <div className="rounded-3xl bg-white p-6 ring-1 ring-slate-200">
          <div className="text-lg font-semibold text-slate-900">No variants yet</div>
            <div className="mt-1 text-sm text-slate-600">No images generated yet. Please try generating again.</div>
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

  const downloadAll = async (variantList?: typeof variants) => {
    const toDownload = variantList || variants
    setDownloadingAll(true)
    trackEvent('download_all_clicked', { count: toDownload.length })
    for (let i = 0; i < toDownload.length; i++) {
      const v = toDownload[i]
      await download(v.url, `meeship_${v.tile_name.replace(/\s+/g, '_')}_${v.variant_label.replace(/\s+/g, '_')}.jpg`)
      await new Promise((r) => setTimeout(r, 200))
    }
    setDownloadingAll(false)
    trackEvent('download_all_success', { count: toDownload.length })
  }

  return (
    <div className="min-h-screen bg-offwhite">
      {confetti && !isStreaming && <ConfettiBurst />}
      <PaymentModal open={paymentOpen} onClose={() => setPaymentOpen(false)} />
      <MeeshoLinkModal 
        open={showMeeshoModal} 
        onClose={() => setShowMeeshoModal(false)}
        onSuccess={() => {
          setShowMeeshoModal(false)
          setMeeshoRefreshKey(k => k + 1)
        }}
      />

      <div className="mx-auto max-w-5xl px-4 pt-8">
        <button
          type="button"
          onClick={handleGenerateAnother}
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
          {isStreaming 
            ? 'Finding your lowest shipping cost...'
            : '✅ Your shipping-optimized images are ready!'
          }
        </motion.div>

        {/* Selected product category */}
        {sscatName && (
          <div className="mt-3 flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
              <span className="text-sm">🏷️</span>
              {sscatName}
            </span>
            {sscatBreadcrumb && (
              <span className="text-xs text-slate-400">{sscatBreadcrumb}</span>
            )}
          </div>
        )}
      </div>

      <div className="mx-auto w-full max-w-5xl px-4 pb-32">
        {/* Progress bar during streaming */}
        {isStreaming && (
          <div className="mt-6">
            <ProgressBar 
              progress={streamingProgress.progress} 
              completed={completed}
              total={totalExpected}
            />
          </div>
        )}

        {/* 🏅 Lowest Shipping Achievement */}
        {!isStreaming && shippingSummary.hasData && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="mt-6 rounded-2xl bg-gradient-to-r from-amber-50 via-yellow-50 to-amber-50 p-4 ring-1 ring-amber-200"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-yellow-500 shadow-md">
                <span className="text-xl">🏅</span>
              </div>
              <div>
                <div className="text-sm font-bold text-amber-900">
                  Lowest shipping found: <span className="text-lg text-emerald-700">₹{shippingSummary.min}</span>
                </div>
                <div className="text-xs text-amber-700">
                  {shippingSummary.max - shippingSummary.min > 0
                    ? `You save ₹${shippingSummary.max - shippingSummary.min} per order vs the highest variant • `
                    : ''}
                  {shippingSummary.count} of {shippingSummary.totalChecked} images checked
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Session Expired Alert */}
        {!isStreaming && shippingSummary.hasSessionExpired && (
          <div className="mt-6">
            <SessionExpiredAlert
              onRelinkClick={() => setShowMeeshoModal(true)}
              message="Your Meesho session expired while generating images. Re-link to see shipping costs."
            />
          </div>
        )}

        {/* Link Meesho CTA if no shipping data and no error */}
        {!isStreaming && variants.length > 0 && !shippingSummary.hasData && !shippingSummary.hasSessionExpired && (
          <div className="mt-6" key={meeshoRefreshKey}>
            <ShippingCostBadge
              sellingPrice={299}
              onLinkClick={() => setShowMeeshoModal(true)}
            />
          </div>
        )}

        {/* ★ TOP 10 Lowest Shipping Cost Images — only verified (with duplicate_pid) */}
        {!isStreaming && shippingSummary.top10.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-full bg-amber-100 px-4 py-2">
                  <span className="text-lg">🏆</span>
                  <span className="font-semibold text-amber-800">Top {shippingSummary.top10.length} Lowest Shipping</span>
                </div>
                <span className="text-sm text-slate-500">{shippingSummary.count} of {shippingSummary.totalChecked} images checked</span>
              </div>
              <button
                type="button"
                onClick={() => downloadAll(shippingSummary.top10)}
                disabled={downloadingAll || downloadState === 'downloading'}
                className="hidden sm:flex items-center gap-2 rounded-xl bg-meesho px-4 py-2.5 text-sm font-semibold text-white hover:bg-meesho/90 transition-colors disabled:opacity-60"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {downloadingAll ? 'Downloading...' : `Download All ${shippingSummary.top10.length}`}
              </button>
            </div>

            <div className="rounded-3xl bg-white p-6 ring-1 ring-slate-200 shadow-sm">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
                {shippingSummary.top10.map((v, rank) => {
                  const badgeColor = rank === 0 ? 'bg-amber-400 text-amber-900' : rank === 1 ? 'bg-slate-300 text-slate-800' : rank === 2 ? 'bg-orange-300 text-orange-900' : 'bg-slate-100 text-slate-700'
                  return (
                    <motion.div
                      key={`top-${v.tile_index}-${v.variant_index}`}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: rank * 0.04 }}
                      className="group relative aspect-square overflow-hidden rounded-xl bg-slate-50 ring-1 ring-slate-200 hover:ring-amber-400 hover:ring-2 transition-all"
                    >
                      <img src={v.url} alt={v.variant_label} className="h-full w-full object-cover" />
                      {/* Rank badge */}
                      <div className={`absolute top-1.5 left-1.5 flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shadow ${badgeColor}`}>
                        {rank + 1}
                      </div>
                      {/* Variant label */}
                      <div className="absolute top-1.5 right-1.5 rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-medium text-white">
                        {v.variant_label}
                      </div>
                      {/* Shipping cost */}
                      <div className="absolute bottom-1 left-1 rounded-md bg-emerald-500/90 px-1.5 py-0.5 text-[10px] font-semibold text-white shadow-sm">
                        🚚 ₹{v.shipping_cost!.shipping_charges}
                      </div>
                      {/* Tile label */}
                      <div className="absolute bottom-1 right-1 rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-medium text-white">
                        {v.tile_name}
                      </div>
                      {/* Hover download overlay */}
                      <div className="absolute inset-0 flex items-center justify-center bg-black/0 opacity-0 group-hover:bg-black/30 group-hover:opacity-100 transition-all">
                        <button
                          type="button"
                          onClick={() => download(v.url, `meeship_top${rank + 1}_${v.tile_name.replace(/\s+/g, '_')}_${v.variant_label.replace(/\s+/g, '_')}.jpg`)}
                          disabled={downloadState === 'downloading'}
                          className="flex items-center gap-1 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 shadow-lg hover:bg-slate-50 transition-colors disabled:opacity-60"
                        >
                          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download
                        </button>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* Fallback: show ALL variants when no verified shipping data (Meesho not linked or per-variant failed) */}
        {!isStreaming && variants.length > 0 && shippingSummary.top10.length === 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-full bg-blue-100 px-4 py-2">
                  <span className="text-lg">🖼️</span>
                  <span className="font-semibold text-blue-800">All {variants.length} Generated Images</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => downloadAll()}
                disabled={downloadingAll || downloadState === 'downloading'}
                className="hidden sm:flex items-center gap-2 rounded-xl bg-meesho px-4 py-2.5 text-sm font-semibold text-white hover:bg-meesho/90 transition-colors disabled:opacity-60"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {downloadingAll ? 'Downloading...' : `Download All ${variants.length}`}
              </button>
            </div>

            <div className="rounded-3xl bg-white p-6 ring-1 ring-slate-200 shadow-sm">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
                {variants.map((v, idx) => (
                  <motion.div
                    key={`all-${v.tile_index}-${v.variant_index}`}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.02 }}
                    className="group relative aspect-square overflow-hidden rounded-xl bg-slate-50 ring-1 ring-slate-200 hover:ring-blue-400 hover:ring-2 transition-all"
                  >
                    <img src={v.url} alt={v.variant_label} className="h-full w-full object-cover" />
                    {/* Variant label */}
                    <div className="absolute top-1.5 left-1.5 rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-medium text-white">
                      {v.variant_label}
                    </div>
                    {/* Shipping cost if available (base rate) */}
                    {v.shipping_cost && (
                      <div className="absolute bottom-1 left-1 rounded-md bg-emerald-500/90 px-1.5 py-0.5 text-[10px] font-semibold text-white shadow-sm">
                        🚚 ₹{v.shipping_cost.shipping_charges}
                      </div>
                    )}
                    {/* Tile label */}
                    <div className="absolute bottom-1 right-1 rounded-md bg-black/50 px-1.5 py-0.5 text-[9px] font-medium text-white">
                      {v.tile_name}
                    </div>
                    {/* Hover download overlay */}
                    <div className="absolute inset-0 flex items-center justify-center bg-black/0 opacity-0 group-hover:bg-black/30 group-hover:opacity-100 transition-all">
                      <button
                        type="button"
                        onClick={() => download(v.url, `meeship_${v.tile_name.replace(/\s+/g, '_')}_${v.variant_label.replace(/\s+/g, '_')}.jpg`)}
                        disabled={downloadState === 'downloading'}
                        className="flex items-center gap-1 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-slate-900 shadow-lg hover:bg-slate-50 transition-colors disabled:opacity-60"
                      >
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Download
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Streaming progress — show while generating */}
        {isStreaming && (
          <div className="mt-6 rounded-3xl bg-white p-6 ring-1 ring-slate-200 shadow-sm">
            <div className="text-lg font-bold text-slate-900">
              {completed} of {totalExpected} Variants
            </div>
            <div className="mt-1 text-sm text-slate-500">
              {streamingProgress.message || 'Generating variants...'}
            </div>
          </div>
        )}

        {/* Tips section */}
        <div className="mt-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 p-4 ring-1 ring-emerald-100">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-emerald-100 p-2">
              <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <div className="text-sm font-semibold text-emerald-800">Pro tips</div>
              <div className="text-sm text-emerald-700">
                <span className="inline-flex items-center gap-1"><span className="text-blue-600">🚚</span> Use <strong>shipping images</strong> for your main product listing — they help Meesho calculate accurate shipping costs.</span>
                <br />
                <span className="inline-flex items-center gap-1 mt-1"><span className="text-purple-600">✨</span> Use <strong>lifestyle images</strong> for ads and social media to boost engagement!</span>
              </div>
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
                    <div className="text-sm text-white/70">1 credit = 1 product optimized</div>
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
                  <div className="text-sm text-white/80">Starting at ₹99 — save ₹1,000+ on shipping</div>
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
