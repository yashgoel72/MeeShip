import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../stores/appStore'

type Props = {
  originalUrl: string | null
  optimizedUrl: string | null
}

function Spinner() {
  return (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 rounded-full border-3 border-slate-100" />
      <motion.div 
        className="absolute inset-0 rounded-full border-3 border-meesho border-t-transparent"
        animate={{ rotate: 360 }}
        transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
      />
    </div>
  )
}

export default function ProcessingOverlay({ originalUrl, optimizedUrl }: Props) {
  const steps = useAppStore((s) => s.steps)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50/30 backdrop-blur-sm">
      <div className="mx-auto w-full max-w-3xl px-4">
        <motion.div 
          className="overflow-hidden rounded-3xl bg-white shadow-xl ring-1 ring-slate-200/60"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Header */}
          <div className="border-b border-slate-100 bg-gradient-to-r from-meesho/5 to-indigo-50/30 px-6 py-5">
            <div className="flex items-center gap-4">
              <Spinner />
              <div className="flex-1">
                <div className="text-xl font-bold text-slate-900">Optimizing Your Product</div>
                <div className="mt-0.5 text-sm text-slate-500">Making it ship cheaper...</div>
              </div>
              <div className="hidden sm:flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-sm ring-1 ring-slate-100">
                <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                <span className="text-sm font-medium text-slate-600">45-60 sec</span>
              </div>
            </div>
          </div>

          {/* Progress Steps */}
          <div className="px-6 py-5">
            <div className="space-y-3">
              {steps.map((step, index) => (
                <motion.div
                  key={step.key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={
                    'flex items-center gap-3 rounded-xl px-4 py-3 transition-all ' +
                    (step.status === 'done' 
                      ? 'bg-emerald-50 ring-1 ring-emerald-100' 
                      : step.status === 'active'
                      ? 'bg-blue-50 ring-1 ring-blue-100'
                      : 'bg-slate-50')
                  }
                >
                  <div className={
                    'flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold transition-all ' +
                    (step.status === 'done'
                      ? 'bg-emerald-500 text-white'
                      : step.status === 'active'
                      ? 'animate-pulse bg-meesho text-white'
                      : 'bg-slate-200 text-slate-400')
                  }>
                    {step.status === 'done' ? (
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : step.status === 'active' ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        ⚡
                      </motion.div>
                    ) : (
                      index + 1
                    )}
                  </div>
                  <div className={
                    'flex-1 text-sm font-medium transition-colors ' +
                    (step.status === 'done'
                      ? 'text-emerald-700'
                      : step.status === 'active'
                      ? 'text-slate-900'
                      : 'text-slate-400')
                  }>
                    {step.label}
                  </div>
                  {step.status === 'active' && (
                    <motion.div
                      className="flex gap-1"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          className="h-1.5 w-1.5 rounded-full bg-meesho"
                          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                        />
                      ))}
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>

          {/* Image Preview */}
          <div className="border-t border-slate-100 bg-slate-50/50 px-6 py-5">
            <div className="grid grid-cols-2 gap-4">
              {/* Original */}
              <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-100">
                <div className="border-b border-slate-100 px-3 py-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Before</span>
                </div>
                <div className="relative aspect-square w-full bg-slate-100">
                  <AnimatePresence>
                    {originalUrl ? (
                      <motion.img
                        key="original"
                        src={originalUrl}
                        className="h-full w-full object-contain p-2"
                        alt="Original"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="h-16 w-16 animate-pulse rounded-2xl bg-slate-200" />
                      </div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Optimized */}
              <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-100">
                <div className="border-b border-slate-100 px-3 py-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-emerald-600">After</span>
                </div>
                <div className="relative aspect-square w-full bg-gradient-to-br from-slate-50 to-blue-50/20">
                  <AnimatePresence>
                    {optimizedUrl ? (
                      <motion.img
                        key="optimized"
                        src={optimizedUrl}
                        className="h-full w-full object-contain p-2"
                        alt="Optimized"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.4 }}
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <motion.div 
                          className="h-16 w-16 rounded-2xl bg-gradient-to-br from-meesho/20 to-indigo-100"
                          animate={{ scale: [1, 1.05, 1] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                        />
                      </div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>

          {/* Savings Indicator */}
          <motion.div 
            className="border-t border-emerald-100 bg-gradient-to-r from-emerald-50 to-teal-50 px-6 py-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100">
                <svg className="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold text-emerald-800">Expected Savings</div>
                <div className="text-xs text-emerald-600">Optimizing for lower shipping slab</div>
              </div>
              <motion.div 
                className="rounded-full bg-white px-4 py-2 shadow-sm"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <span className="text-lg font-bold text-emerald-600">₹10-20</span>
                <span className="ml-1 text-xs text-slate-500">/order</span>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}
