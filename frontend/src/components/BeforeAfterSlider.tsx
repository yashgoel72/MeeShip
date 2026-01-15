import { motion, useMotionValue } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'

type Props = {
  beforeUrl: string
  afterUrl: string
}

export default function BeforeAfterSlider({ beforeUrl, afterUrl }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const x = useMotionValue(0)
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const ro = new ResizeObserver(() => {
      const rect = el.getBoundingClientRect()
      setWidth(rect.width)
      x.set(rect.width / 2)
    })

    ro.observe(el)
    return () => ro.disconnect()
  }, [x])

  const clip = width > 0 ? `inset(0 ${Math.max(0, width - x.get())}px 0 0)` : 'inset(0 50% 0 0)'

  return (
    <div ref={containerRef} className="relative mx-auto w-full overflow-hidden rounded-3xl bg-white ring-1 ring-slate-200">
      <div className="absolute left-4 top-4 z-10 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
        Original
      </div>
      <div className="absolute right-4 top-4 z-10 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
        Optimized
      </div>

      <div className="relative aspect-square w-full">
        <img src={beforeUrl} alt="Before" className="absolute inset-0 h-full w-full object-contain" />
        <div className="absolute inset-0" style={{ clipPath: clip }}>
          <img src={afterUrl} alt="After" className="h-full w-full object-contain" />
        </div>

        <motion.div
          className="absolute top-0 h-full w-0.5 bg-meesho"
          style={{ left: x }}
        />

        <motion.button
          type="button"
          aria-label="Drag to compare"
          className="absolute top-1/2 -translate-y-1/2 rounded-full bg-white p-2 shadow-sm ring-1 ring-slate-200"
          style={{ left: x, x: '-50%' }}
          drag="x"
          dragConstraints={containerRef}
          dragElastic={0}
          whileTap={{ scale: 0.98 }}
          onDrag={() => {
            const el = containerRef.current
            if (!el) return
            const rect = el.getBoundingClientRect()
            const current = x.get()
            const clamped = Math.max(0, Math.min(rect.width, current))
            x.set(clamped)
          }}
        >
          <div className="h-5 w-5 rounded-full bg-meesho" />
        </motion.button>
      </div>
    </div>
  )
}
