import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll } from 'framer-motion'
import { Dialog } from '@headlessui/react'
import UploadZone from '../components/UploadZone'
import CategoryPicker from '../components/CategoryPicker'
import UpgradeBanner from '../components/UpgradeBanner'
import Footer from '../components/Footer'
import MeeshoLinkModal from '../components/MeeshoLinkModal'
import HowItWorks from '../components/HowItWorks'
import TrustBar from '../components/TrustBar'
import { useImageUpload } from '../hooks/useImageUpload'
import { useStreamingOptimization } from '../hooks/useStreamingOptimization'
import { useAuth } from '../context/AuthContext'
import { useAppStore } from '../stores/appStore'
import { getMeeshoStatus, validateMeeshoSession } from '../services/meeshoApi'

interface HeaderProps {
  onSignIn: () => void
  meeshoLinked: boolean | null
  onMeeshoLinkClick: () => void
}

function Header({ onSignIn, meeshoLinked, onMeeshoLinkClick }: HeaderProps) {
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()

  useEffect(() => {
    const unsub = scrollY.on('change', (v) => setScrolled(v > 8))
    return () => unsub()
  }, [scrollY])

  return (
    <header className={
      'fixed inset-x-0 top-0 z-40 transition-colors ' +
      (scrolled ? 'bg-white/90 backdrop-blur ring-1 ring-slate-200' : 'bg-transparent')
    }>
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link to="/" className="flex items-center gap-3">
          <div>
            <div className="text-sm font-extrabold tracking-tight text-slate-900 font-display">
              MeeShip
              <span className="ml-2 inline-block h-0.5 w-8 align-middle bg-amber-500" />
            </div>
            <div className="hidden text-[10px] font-medium text-slate-500 sm:block">
              Meesho का Smart Shipping Tool
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-5 sm:flex">
          <Link to="/" className="text-sm font-medium text-meesho">
            Home
          </Link>
          <Link to="/contact" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
            Contact
          </Link>
        </nav>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              {/* Meesho Link Status */}
              {meeshoLinked !== null && (
                <button
                  type="button"
                  onClick={onMeeshoLinkClick}
                  className={`hidden items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 transition-colors sm:flex ${
                    meeshoLinked
                      ? 'bg-pink-50 text-pink-700 ring-pink-200 hover:bg-pink-100'
                      : 'bg-gray-50 text-gray-600 ring-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  {meeshoLinked ? 'Meesho ✓' : 'Link Meesho'}
                </button>
              )}
              {/* Credit Balance Badge */}
              {typeof user?.credits === 'number' && (
                <div className="hidden items-center gap-2 sm:flex">
                  <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
                    {user.credits} credits
                  </div>
                  <Link
                    to="/pricing"
                    className="rounded-full bg-meesho/10 px-3 py-1 text-xs font-semibold text-meesho ring-1 ring-meesho/20 hover:bg-meesho/20 transition-colors"
                  >
                    Buy Credits
                  </Link>
                </div>
              )}
              {user?.isUpgraded && (
                <div className="hidden rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-100 sm:block">
                  Pro Plan Active
                </div>
              )}
              <div className="hidden text-xs text-slate-600 sm:block">{user?.email}</div>
              <button
                type="button"
                onClick={logout}
                  className="rounded-xl px-3 py-2 text-sm font-semibold bg-slate-700 text-white hover:bg-slate-800 transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={onSignIn}
                className="rounded-xl px-3 py-2 text-sm font-semibold bg-slate-700 text-white hover:bg-slate-800 transition-colors"
            >
              Sign in
            </button>
          )}
        </div>
      </div>

    </header>
  )
}

function SignInModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { loginWithKinde } = useAuth()

  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-slate-900/20" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-md rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <Dialog.Title className="text-lg font-bold text-slate-900">Sign in to MeeShip</Dialog.Title>
          <div className="mt-1 text-sm text-slate-600">
            Secure login with email verification. No password needed!
          </div>

          <div className="mt-6 space-y-3">
            <button
              type="button"
              onClick={loginWithKinde}
              className="w-full rounded-2xl bg-meesho text-white px-5 py-3.5 text-sm font-semibold transition-all hover:bg-meesho-dark shadow-sm hover:shadow-md flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Sign in with Email OTP
            </button>

            <div className="text-xs text-center text-slate-500 mt-4">
              We'll send a one-time code to verify your email
            </div>

            <button
              type="button"
              onClick={onClose}
              className="w-full rounded-2xl px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}

export default function LandingScreen() {
  const { isAuthenticated, user } = useAuth()
  const { acceptFile, compressing, compressError } = useImageUpload()
  const { startStreaming } = useStreamingOptimization()
  const originalFile = useAppStore((s) => s.originalFile)
  const compressedFile = useAppStore((s) => s.compressedFile)
  const originalPreviewUrl = useAppStore((s) => s.originalPreviewUrl)
  const sscatId = useAppStore((s) => s.sscatId)
  const error = useAppStore((s) => s.error)
  const [signInOpen, setSignInOpen] = useState(false)

  // Meesho link state — shared between Header pill and body banner
  const [meeshoLinked, setMeeshoLinked] = useState<boolean | null>(null)
  const [meeshoSessionExpired, setMeeshoSessionExpired] = useState(false)
  const [showMeeshoModal, setShowMeeshoModal] = useState(false)

  // Check Meesho link status + session validity when authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      setMeeshoLinked(null)
      setMeeshoSessionExpired(false)
      return
    }

    const checkMeesho = async () => {
      try {
        const status = await getMeeshoStatus()
        setMeeshoLinked(status.linked)
        // If linked, check if session is still valid
        if (status.linked) {
          try {
            const validation = await validateMeeshoSession()
            if (!validation.valid && validation.error_code === 'SESSION_EXPIRED') {
              setMeeshoSessionExpired(true)
            } else {
              setMeeshoSessionExpired(false)
            }
          } catch {
            // Validation endpoint may not exist yet — treat as valid
            setMeeshoSessionExpired(false)
          }
        }
      } catch {
        setMeeshoLinked(false)
      }
    }

    checkMeesho()
  }, [isAuthenticated])

  const handleMeeshoLinkSuccess = () => {
    setShowMeeshoModal(false)
    setMeeshoLinked(true)
    setMeeshoSessionExpired(false)
  }

  // Listen for meesho-link-required events from streaming hook (e.g. 403 from backend)
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.reason === 'MEESHO_NOT_LINKED') {
        setMeeshoLinked(false)
      } else if (detail?.reason === 'MEESHO_SESSION_EXPIRED') {
        setMeeshoSessionExpired(true)
      }
      setShowMeeshoModal(true)
    }
    window.addEventListener('meesho-link-required', handler)
    return () => window.removeEventListener('meesho-link-required', handler)
  }, [])

  const canGenerate = useMemo(() => {
    return !!originalFile && !!compressedFile && !compressing && sscatId !== null
  }, [compressedFile, compressing, originalFile, sscatId])

  // Meesho must be linked with a valid session to generate
  const meeshoReady = meeshoLinked === true && !meeshoSessionExpired

  // Show Meesho banner: not linked, or session expired
  const showMeeshoBanner = isAuthenticated && meeshoLinked !== null && (!meeshoLinked || meeshoSessionExpired)

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-blue-50/30">
      <Header
        onSignIn={() => setSignInOpen(true)}
        meeshoLinked={meeshoLinked}
        onMeeshoLinkClick={() => setShowMeeshoModal(true)}
      />

      <div className="mx-auto max-w-5xl px-4 pt-24">
        <div className="min-h-[80vh] py-10 sm:py-16">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-meesho/10 px-4 py-1.5 text-sm font-semibold text-meesho">
              <span className="flex h-2 w-2 animate-pulse rounded-full bg-meesho" />
              1 Photo → ₹10-20 Saved Per Order
            </div>
            <h1 className="font-display text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Save <span className="bg-gradient-to-r from-emerald-500 to-teal-500 bg-clip-text text-transparent">₹10-20</span> on Every Meesho Order
            </h1>
            <div className="mt-5 text-lg text-slate-600 sm:text-xl">
              Upload 1 photo → We test <span className="font-semibold text-slate-900">30 image variations</span> → Find your cheapest shipping
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-2 sm:gap-3">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-100 sm:text-sm sm:px-4 sm:py-2">
                <span className="flex h-2 w-2 rounded-full bg-emerald-500" />
                2,000+ sellers saving daily
              </div>
              <div className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700 ring-1 ring-amber-100 sm:text-sm sm:px-4 sm:py-2">
                💰 ₹4.2 Cr+ saved so far
              </div>
              <TrustBar />
            </div>
          </div>

          {/* Meesho Account Link Banner */}
          {showMeeshoBanner && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className={`mx-auto mt-8 max-w-2xl rounded-2xl p-4 shadow-sm ${
                meeshoSessionExpired
                  ? 'bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 ring-1 ring-amber-200'
                  : 'bg-gradient-to-r from-pink-50 via-rose-50 to-pink-50 ring-1 ring-pink-200'
              }`}
            >
              <div className="flex items-center gap-4">
                <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full shadow-md ${
                  meeshoSessionExpired
                    ? 'bg-gradient-to-br from-amber-400 to-orange-500'
                    : 'bg-gradient-to-br from-pink-400 to-rose-500'
                }`}>
                  <span className="text-xl">{meeshoSessionExpired ? '⚠️' : '🔗'}</span>
                </div>
                <div className="flex-1">
                  <div className={`text-sm font-bold ${
                    meeshoSessionExpired ? 'text-amber-900' : 'text-pink-900'
                  }`}>
                    {meeshoSessionExpired
                      ? 'Your Meesho session has expired'
                      : 'Link your Meesho Supplier Account'
                    }
                  </div>
                  <div className={`mt-0.5 text-xs ${
                    meeshoSessionExpired ? 'text-amber-700' : 'text-pink-700'
                  }`}>
                    {meeshoSessionExpired
                      ? 'Re-link to see real shipping costs for every generated image'
                      : 'See real Meesho shipping costs for each image — find which ones save you the most!'
                    }
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowMeeshoModal(true)}
                  className={`shrink-0 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors ${
                    meeshoSessionExpired
                      ? 'bg-amber-500 text-white hover:bg-amber-600'
                      : 'bg-pink-500 text-white hover:bg-pink-600'
                  }`}
                >
                  {meeshoSessionExpired ? '🔄 Re-link Account' : '🔗 Link Meesho'}
                </button>
              </div>
            </motion.div>
          )}

          <div className="mt-10">
            <UploadZone
              disabled={false}
              onFileAccepted={(file) => {
                acceptFile(file)
              }}
            />

            {/* Product Category Picker */}
            <div className="mt-6">
              <CategoryPicker />
            </div>

            {/* Upgrade Banner for users with low/no credits */}
            {isAuthenticated && (
              <div className="mt-6">
                <UpgradeBanner 
                  credits={user?.credits} 
                  expiresAt={user?.creditsExpiresAt} 
                />
              </div>
            )}

            {(compressError || error) && (
              <div className="mx-auto mt-4 w-full max-w-2xl rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {compressError || error}
                <div className="mt-1 text-xs text-rose-700/80">Try different angle/lighting, then reupload.</div>
              </div>
            )}

            {originalPreviewUrl && (
              <motion.div
                className="mx-auto mt-6 w-full max-w-2xl overflow-hidden rounded-3xl bg-white ring-1 ring-slate-200"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <div className="px-4 py-3 text-xs font-semibold text-slate-700">Preview</div>
                <img src={originalPreviewUrl} alt="Preview" className="max-h-[420px] w-full object-contain" />
              </motion.div>
            )}

            <div className="mx-auto mt-6 w-full max-w-2xl">

              <motion.button
                type="button"
                whileHover={canGenerate && !compressing && meeshoReady ? { scale: 1.02, y: -2 } : {}}
                whileTap={canGenerate && !compressing && meeshoReady ? { scale: 0.98 } : {}}
                onClick={() => {
                  // Skip auth check in development
                  const isDev = import.meta.env.DEV
                  if (!isDev && !isAuthenticated) {
                    setSignInOpen(true)
                    return
                  }
                  // Require Meesho account link
                  if (!meeshoReady) {
                    setShowMeeshoModal(true)
                    return
                  }
                  if (!canGenerate || !originalFile) return
                  startStreaming(originalFile)
                }}
                disabled={!canGenerate || compressing}
                className={
                  'group w-full rounded-2xl px-6 py-4 text-lg font-bold transition-all duration-300 ' +
                  (canGenerate && !compressing
                    ? meeshoReady
                      ? 'bg-gradient-to-r from-meesho via-pink-500 to-purple-600 text-white shadow-xl shadow-meesho/25 hover:shadow-2xl hover:shadow-meesho/30'
                      : 'bg-gradient-to-r from-pink-300 via-pink-400 to-purple-400 text-white shadow-lg cursor-pointer'
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none')
                }
              >
                <span className="flex items-center justify-center gap-2">
                  {compressing ? (
                    <>
                      <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Preparing...
                    </>
                  ) : (
                    <>
                      <span className="text-xl">⚡</span>
                      {!isAuthenticated
                        ? 'Sign in to Get Started'
                        : !meeshoReady
                          ? '� Start Saving on Shipping'
                          : (user?.credits ?? 0) > 0 ? 'Find My Lowest Shipping' : 'Try Free — See Your Savings'
                      }
                      <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </>
                  )}
                </span>
              </motion.button>

              {/* Meesho link hint below CTA */}
              {isAuthenticated && !meeshoReady && !compressing && (
                <div className="mt-2 flex items-center justify-center gap-1.5 text-xs text-slate-400">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  Quick one-time Meesho login required · Your password is never stored
                </div>
              )}

              {compressing && (
                <div className="mt-2 text-center text-sm text-slate-500">Preparing your image...</div>
              )}
            </div>
          </div>

          {/* === BELOW-THE-FOLD: Explanation & Social Proof === */}

          {/* How It Works - Animated Step Explainer */}
          <HowItWorks />

          {/* ROI Calculator */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mx-auto mt-12 max-w-2xl"
          >
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 shadow-sm ring-1 ring-emerald-200">
              <div className="absolute -top-12 -right-12 w-32 h-32 bg-emerald-200/40 rounded-full blur-2xl" />
              <div className="absolute -bottom-12 -left-12 w-32 h-32 bg-teal-200/40 rounded-full blur-2xl" />
              <div className="relative">
                <div className="px-4 py-3 bg-emerald-100/60 backdrop-blur-sm text-center border-b border-emerald-200/50">
                  <span className="text-sm font-semibold text-emerald-800 flex items-center justify-center gap-2">
                    <span className="text-base">💡</span> Your Potential Savings
                  </span>
                </div>
                <div className="p-6">
                  <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center sm:gap-6">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-slate-900">₹10</div>
                      <div className="text-xs text-slate-600 mt-1">saved per order</div>
                    </div>
                    <div className="text-2xl text-emerald-400 font-light">×</div>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-slate-900">1,000</div>
                      <div className="text-xs text-slate-600 mt-1">orders/month</div>
                    </div>
                    <div className="text-2xl text-emerald-400 font-light">=</div>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-emerald-600">₹10,000</div>
                      <div className="text-xs font-medium text-emerald-600 mt-1">monthly profit</div>
                    </div>
                  </div>
                  <div className="mt-5 flex items-center justify-center gap-2 rounded-xl bg-white/60 backdrop-blur-sm px-4 py-2.5 text-sm text-slate-700 ring-1 ring-emerald-200/50">
                    <span className="text-blue-500">↩️</span>
                    <span><strong>Returns?</strong> You save 2x on shipping (forward + return). More returns = more savings!</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Testimonials */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="mx-auto mt-16 max-w-5xl"
          >
            <div className="mb-6 text-center">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Real savings from sellers</span>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {[
                { amount: '₹65,000+', quote: 'Total saved in 3 months on 5000 orders', name: 'Priya', city: 'Delhi', initials: 'P', color: 'bg-pink-100 text-pink-600' },
                { amount: '₹110 → ₹71', quote: 'Saree shipping cut by ₹39!', name: 'Rahul', city: 'Surat', initials: 'R', color: 'bg-blue-100 text-blue-600' },
                { amount: '₹68 → ₹52', quote: 'Every t-shirt order saves ₹16', name: 'Vikram', city: 'Mumbai', initials: 'V', color: 'bg-emerald-100 text-emerald-600' },
              ].map((t, idx) => (
                <motion.div 
                  key={idx}
                  whileHover={{ y: -4 }}
                  className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100 transition-shadow hover:shadow-lg"
                >
                  <div className="flex items-start gap-3 mb-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-full ${t.color} text-sm font-bold`}>
                      {t.initials}
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-900">{t.name}</div>
                      <div className="text-xs text-slate-500">{t.city}</div>
                    </div>
                  </div>
                  <div className="mb-2 text-2xl font-bold text-emerald-600">{t.amount}</div>
                  <div className="text-sm text-slate-600">"{t.quote}"</div>
                  <div className="mt-3 flex gap-0.5">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Footer */}
      <Footer />

      <SignInModal open={signInOpen} onClose={() => setSignInOpen(false)} />
      <MeeshoLinkModal
        open={showMeeshoModal}
        onClose={() => setShowMeeshoModal(false)}
        onSuccess={handleMeeshoLinkSuccess}
      />
    </div>
  )
}
