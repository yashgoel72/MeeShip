import { motion } from 'framer-motion'

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.2, duration: 0.5, ease: 'easeOut' as const },
  }),
}

const arrowVariants = {
  hidden: { opacity: 0, scale: 0.5 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { delay: 0.3, duration: 0.4, ease: 'easeOut' as const },
  },
}

export default function BeforeAfterShowcase() {
  return (
    <motion.section
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-60px' }}
      className="mx-auto mt-16 max-w-4xl"
    >
      {/* Section header */}
      <div className="mb-8 text-center">
        <span className="inline-flex items-center gap-2 rounded-full bg-violet-50 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-violet-600 ring-1 ring-violet-200">
          <span className="text-sm">✨</span> See it in action
        </span>
        <h2 className="mt-3 font-display text-2xl font-bold text-slate-900 sm:text-3xl">
          One Photo. Real Savings.
        </h2>
        <p className="mt-2 text-sm text-slate-500 sm:text-base">
          Upload your product photo — we find the image that gets the cheapest Meesho shipping
        </p>
      </div>

      {/* Before / After cards */}
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-stretch sm:gap-0">
        {/* BEFORE — Input photo */}
        <motion.div
          custom={0}
          variants={cardVariants}
          className="group relative w-full overflow-hidden rounded-2xl bg-white shadow-md ring-1 ring-slate-200 transition-shadow hover:shadow-xl sm:w-[45%]"
        >
          {/* Label */}
          <div className="flex items-center gap-2 bg-slate-50 px-4 py-2.5 border-b border-slate-100">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs">
              📷
            </span>
            <span className="text-sm font-semibold text-slate-700">You upload this</span>
          </div>
          {/* Image */}
          <div className="relative aspect-square overflow-hidden bg-slate-50">
            <img
              src="/showcase-input.jpg"
              alt="Product photo — black shoes with diamond pattern"
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
            {/* Upload icon overlay */}
            <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors group-hover:bg-black/5">
              <div className="rounded-full bg-white/80 p-3 opacity-0 shadow-lg backdrop-blur-sm transition-opacity group-hover:opacity-100">
                <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>
          {/* Caption */}
          <div className="px-4 py-3 text-center">
            <span className="text-xs font-medium text-slate-400">Any product photo — taken on your phone</span>
          </div>
        </motion.div>

        {/* Arrow connector */}
        <motion.div
          variants={arrowVariants}
          className="flex shrink-0 items-center justify-center sm:w-[10%]"
        >
          {/* Desktop: horizontal arrow */}
          <div className="hidden sm:flex flex-col items-center gap-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-violet-500 to-purple-600 shadow-lg shadow-violet-200">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
            <span className="text-[10px] font-semibold text-violet-500 uppercase tracking-wider">AI Magic</span>
          </div>
          {/* Mobile: vertical arrow */}
          <div className="flex sm:hidden items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-b from-violet-500 to-purple-600 shadow-lg shadow-violet-200">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </div>
            <span className="text-xs font-semibold text-violet-500">AI Magic</span>
          </div>
        </motion.div>

        {/* AFTER — Result screenshot */}
        <motion.div
          custom={1}
          variants={cardVariants}
          className="group relative w-full overflow-hidden rounded-2xl bg-white shadow-md ring-1 ring-slate-200 transition-shadow hover:shadow-xl sm:w-[45%]"
        >
          {/* Label */}
          <div className="flex items-center gap-2 bg-emerald-50 px-4 py-2.5 border-b border-emerald-100">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs">
              🏆
            </span>
            <span className="text-sm font-semibold text-emerald-700">You get this</span>
          </div>
          {/* Image */}
          <div className="relative aspect-square overflow-hidden bg-gradient-to-b from-amber-50/50 to-slate-50">
            <img
              src="/showcase-result.png"
              alt="MeeShip result — Top 10 lowest shipping images with prices"
              className="h-full w-full object-contain p-2 transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />
            {/* Shimmer overlay on hover */}
            <div className="absolute inset-0 bg-gradient-to-t from-emerald-900/10 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
          </div>
          {/* Caption */}
          <div className="px-4 py-3 text-center">
            <span className="text-xs font-medium text-slate-400">Top 10 images ranked by lowest Meesho shipping</span>
          </div>
        </motion.div>
      </div>

      {/* Savings callout */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.6, duration: 0.4 }}
        className="mt-6 flex justify-center"
      >
        <div className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 px-5 py-3 shadow-sm ring-1 ring-emerald-200">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500 text-white shadow-md">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-bold text-emerald-800">
              Lowest shipping: ₹81 — <span className="text-emerald-600">saved ₹81</span> vs highest
            </div>
            <div className="text-xs text-emerald-600/70">
              20 image variations tested automatically in under 2 minutes
            </div>
          </div>
        </div>
      </motion.div>
    </motion.section>
  )
}
