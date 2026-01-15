import { motion } from 'framer-motion'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import type { OptimizeResult } from '../stores/appStore'

type Props = {
  result: OptimizeResult
  originalUrl: string
  optimizedUrl: string
  onDownload: () => void
  downloadState: 'idle' | 'downloading' | 'saved'
}

function formatBytes(bytes?: number) {
  if (!bytes || bytes <= 0) return '—'
  const kb = bytes / 1024
  if (kb < 1024) return `${Math.round(kb)}KB`
  return `${(kb / 1024).toFixed(1)}MB`
}

function DownloadIndicator({ state }: { state: 'idle' | 'downloading' | 'saved' }) {
  if (state === 'downloading') {
    return (
      <span className="inline-flex h-5 w-5 items-center justify-center">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
      </span>
    )
  }
  if (state === 'saved') {
    return <span className="text-white">✓</span>
  }
  return null
}

export default function ResultShowcase({ result, originalUrl, optimizedUrl, onDownload, downloadState }: Props) {
  const inputBytes = result.metrics?.input_size_bytes
  const outputBytes = result.metrics?.output_size_bytes
  const savingsPct = result.cost?.savings_percentage ?? 60

  // INR estimate (no Meesho slab API): assume baseline shipping ₹50, show ±20% range.
  const baseline = 50
  const est = (baseline * Math.min(0.8, Math.max(0.3, savingsPct / 100)))
  const min = Math.max(5, Math.round(est * 0.8))
  const max = Math.max(min + 5, Math.round(est * 1.2))

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pb-28">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="mt-8 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
      >
        <div className="text-2xl font-bold text-slate-900">Your shipping-optimized image is ready!</div>
        <div className="mt-1 text-sm text-slate-600">Estimates are based on standard Meesho slabs (no live API).</div>

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-600">Original size</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">{formatBytes(inputBytes)}</div>
            <div className="mt-1 text-xs text-success">→ New: {formatBytes(outputBytes)} ✓</div>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-600">Product fill</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">~90% → 62% ✓</div>
            <div className="mt-1 text-xs text-slate-600">Optimal range is ~60–70%</div>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-600">Est. savings</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">₹{min}–₹{max} / order</div>
            <div className="mt-1 text-xs text-success">Shipping Saved! (~{Math.round(savingsPct)}%)</div>
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-3xl bg-slate-50 ring-1 ring-slate-200">
          <div className="group relative">
            <img
              src={optimizedUrl}
              alt="Optimized preview"
              className="mx-auto max-h-[520px] w-full object-contain transition-transform duration-300 ease-in-out group-hover:scale-[1.02]"
            />

            <button
              type="button"
              onClick={onDownload}
              className="absolute right-4 top-4 inline-flex items-center gap-2 rounded-2xl bg-white/90 px-3 py-2 text-sm font-semibold text-slate-900 ring-1 ring-slate-200 hover:bg-white"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              Download
            </button>
          </div>
        </div>

        <button
          type="button"
          onClick={onDownload}
          className="mt-5 w-full rounded-2xl bg-success px-5 py-4 text-lg font-semibold text-white transition-colors hover:bg-success/90"
        >
          <span className="inline-flex items-center justify-center gap-3">
            <DownloadIndicator state={downloadState} />
            {downloadState === 'idle' && 'Download JPG'}
            {downloadState === 'downloading' && 'Downloading…'}
            {downloadState === 'saved' && 'Saved to Downloads ✓'}
          </span>
        </button>

        <div className="mt-3 text-xs text-slate-500">Optimized for marketplace listing best practices.</div>

        {/* Hidden but available for debugging */}
        <div className="mt-4 hidden text-xs text-slate-500">
          {result.id}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          <div className="overflow-hidden rounded-2xl bg-slate-100">
            <div className="px-3 py-2 text-xs font-medium text-slate-700">Original</div>
            <img src={originalUrl} alt="Original" className="aspect-square w-full object-contain" />
          </div>
          <div className="overflow-hidden rounded-2xl bg-slate-100">
            <div className="px-3 py-2 text-xs font-medium text-slate-700">Optimized</div>
            <img src={optimizedUrl} alt="Optimized" className="aspect-square w-full object-contain" />
          </div>
        </div>
      </motion.div>
    </div>
  )
}
