import { motion } from 'framer-motion'

const steps = [
  {
    number: '1',
    title: 'Upload Your Product Photo',
    description: 'Drop any product image — we handle the rest',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
    color: 'from-blue-500 to-indigo-600',
    bgLight: 'bg-blue-50',
    ringColor: 'ring-blue-100',
  },
  {
    number: '2',
    title: 'Quick Meesho Login',
    description: 'One-time secure login — password never stored',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    color: 'from-pink-500 to-purple-600',
    bgLight: 'bg-pink-50',
    ringColor: 'ring-pink-100',
  },
  {
    number: '3',
    title: 'Get Lowest Shipping',
    description: 'We test 30 image variations to find your cheapest rate',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
      </svg>
    ),
    color: 'from-emerald-500 to-teal-600',
    bgLight: 'bg-emerald-50',
    ringColor: 'ring-emerald-100',
  },
]

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.2 },
  },
}

const stepVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' as const },
  },
}

const lineVariants = {
  hidden: { scaleX: 0 },
  visible: {
    scaleX: 1,
    transition: { duration: 0.6, ease: 'easeOut' as const, delay: 0.3 },
  },
}

export default function HowItWorks() {
  return (
    <section className="mx-auto mt-14 max-w-3xl">
      {/* Section header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        className="text-center mb-10"
      >
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-slate-500 ring-1 ring-slate-200">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          3 Simple Steps
        </span>
        <h2 className="mt-3 text-2xl font-extrabold text-slate-900 sm:text-3xl">
          How It Works
        </h2>
        <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
          From upload to savings in under 2 minutes
        </p>
      </motion.div>

      {/* Steps */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-60px' }}
        className="relative"
      >
        {/* Desktop connecting line */}
        <div className="hidden sm:block absolute top-[3.5rem] left-[16%] right-[16%] h-[2px] z-0">
          <motion.div
            variants={lineVariants}
            className="h-full bg-gradient-to-r from-blue-200 via-pink-200 to-emerald-200 origin-left rounded-full"
          />
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 sm:gap-4">
          {steps.map((step, idx) => (
            <motion.div
              key={step.number}
              variants={stepVariants}
              className="relative z-10 flex flex-col items-center text-center"
            >
              {/* Icon circle */}
              <motion.div
                whileHover={{ scale: 1.08, rotate: 3 }}
                transition={{ type: 'spring', stiffness: 300 }}
                className={`relative flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-2xl bg-gradient-to-br ${step.color} text-white shadow-lg`}
              >
                {step.icon}
                {/* Step number badge */}
                <div className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs font-bold text-slate-700 shadow-md ring-2 ring-white">
                  {step.number}
                </div>
              </motion.div>

              {/* Mobile connecting arrow (between cards) */}
              {idx < steps.length - 1 && (
                <div className="sm:hidden flex justify-center my-2 text-slate-300">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
              )}

              {/* Text */}
              <h3 className="mt-4 text-base font-bold text-slate-900">{step.title}</h3>
              <p className="mt-1.5 text-sm text-slate-500 max-w-[200px] leading-relaxed">{step.description}</p>

              {/* Trust micro-badge on step 2 */}
              {step.number === '2' && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.6, duration: 0.3 }}
                  className="mt-3 inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-1 text-[11px] font-semibold text-green-700 ring-1 ring-green-200"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                  AES-256 Encrypted
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Result teaser */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.5, duration: 0.5 }}
        className="mt-10 flex items-center justify-center gap-3"
      >
        <div className="flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 ring-1 ring-emerald-200">
          <span className="text-lg">🎯</span>
          <span className="text-sm font-semibold text-emerald-700">Result:</span>
          <span className="text-sm text-emerald-600">Optimized images + exact shipping cost for each</span>
        </div>
      </motion.div>
    </section>
  )
}
