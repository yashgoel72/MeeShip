import { useEffect, useMemo, useState } from 'react'
import { motion, useScroll } from 'framer-motion'
import { Dialog } from '@headlessui/react'
import UploadZone from '../components/UploadZone'
import UpgradeBanner from '../components/UpgradeBanner'
import { useImageUpload } from '../hooks/useImageUpload'
import { useFluxGeneration } from '../hooks/useFluxGeneration'
import { useAuth } from '../context/AuthContext'
import { useAppStore } from '../stores/appStore'

function Header({ onSignIn }: { onSignIn: () => void }) {
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()

  useEffect(() => {
    const unsub = scrollY.on('change', (v) => setScrolled(v > 8))
    return () => unsub()
  }, [scrollY])

  return (
    <div className={
      'fixed inset-x-0 top-0 z-40 transition-colors ' +
      (scrolled ? 'bg-white/90 backdrop-blur ring-1 ring-slate-200' : 'bg-transparent')
    }>
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <div className="text-sm font-extrabold tracking-tight text-slate-900">
          MeeshoShipOptimizer
          <span className="ml-2 inline-block h-0.5 w-10 align-middle bg-underline" />
        </div>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              {/* Credit Balance Badge */}
              {typeof user?.credits === 'number' && (
                <div className="hidden rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200 sm:block">
                  {user.credits} credits
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
    </div>
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
  const { run } = useFluxGeneration()
  const originalFile = useAppStore((s) => s.originalFile)
  const compressedFile = useAppStore((s) => s.compressedFile)
  const originalPreviewUrl = useAppStore((s) => s.originalPreviewUrl)
  const error = useAppStore((s) => s.error)
  const [signInOpen, setSignInOpen] = useState(false)

  const canGenerate = useMemo(() => {
    return !!originalFile && !!compressedFile && !compressing
  }, [compressedFile, compressing, originalFile])

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-blue-50/30">
      <Header onSignIn={() => setSignInOpen(true)} />

      <div className="mx-auto max-w-5xl px-4 pt-24">
        <div className="min-h-[80vh] py-10 sm:py-16">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Save <span className="bg-gradient-to-r from-emerald-500 to-teal-500 bg-clip-text text-transparent">₹8-15</span> on Every Meesho Order
            </h1>
            <div className="mt-5 text-lg text-slate-600 sm:text-xl">
              Upload your product photo → Get shipping-optimized image → Pay less on every sale
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100">
                <span className="flex h-2 w-2 rounded-full bg-emerald-500" />
                2,000+ sellers saving daily
              </div>
              <div className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 ring-1 ring-amber-100">
                💰 ₹4.2 Cr+ saved so far
              </div>
            </div>
          </div>

          <div className="mt-10">
            <UploadZone
              disabled={false}
              onFileAccepted={(file) => {
                acceptFile(file)
              }}
            />

            {/* Outcome-focused benefits */}
            <div className="mx-auto mt-6 flex max-w-2xl flex-wrap justify-center gap-2">
              {[
                { emoji: '📦', text: 'Lower shipping slab' },
                { emoji: '💵', text: 'More profit per sale' },
                { emoji: '⚡', text: 'Ready in seconds' },
                { emoji: '✅', text: 'Meesho-compliant' },
              ].map((b) => (
                <div key={b.text} className="flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-sm text-slate-600 shadow-sm ring-1 ring-slate-100">
                  <span>{b.emoji}</span>
                  {b.text}
                </div>
              ))}
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

              <button
                type="button"
                onClick={() => {
                  if (!isAuthenticated) {
                    setSignInOpen(true)
                    return
                  }
                  if (!canGenerate) return
                  run()
                }}
                disabled={!canGenerate || compressing}
                className={
                  'w-full rounded-2xl px-5 py-4 text-lg font-semibold transition-all shadow-lg ' +
                  (canGenerate && !compressing
                    ? 'bg-gradient-to-r from-meesho to-indigo-600 text-white hover:shadow-xl'
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none')
                }
              >
                {compressing ? 'Preparing...' : ((user?.credits ?? 0) > 0 ? '⚡ Get Optimized Image' : '⚡ Try Free')}
              </button>

              {compressing && (
                <div className="mt-2 text-center text-sm text-slate-500">Preparing your image...</div>
              )}
            </div>
          </div>

          {/* Testimonials - outcome focused */}
          <div className="mx-auto mt-14 max-w-5xl">
            <div className="mb-4 text-center text-sm font-medium uppercase tracking-wider text-slate-400">
              Real savings from sellers
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
                <div className="mb-2 text-2xl font-bold text-emerald-600">₹1.2 Cr</div>
                <div className="text-sm text-slate-900">"Total saved across 15 lakh orders"</div>
                <div className="mt-2 text-sm text-slate-500">Rahul • Surat</div>
              </div>
              <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
                <div className="mb-2 text-2xl font-bold text-emerald-600">₹23 → ₹15</div>
                <div className="text-sm text-slate-900">"Shipping dropped on every order"</div>
                <div className="mt-2 text-sm text-slate-500">Priya • Delhi</div>
              </div>
              <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100">
                <div className="mb-2 text-2xl font-bold text-emerald-600">₹45 → ₹22</div>
                <div className="text-sm text-slate-900">"Same product, half the shipping"</div>
                <div className="mt-2 text-sm text-slate-500">Vikram • Mumbai</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <SignInModal open={signInOpen} onClose={() => setSignInOpen(false)} />

    </div>
  )
}
