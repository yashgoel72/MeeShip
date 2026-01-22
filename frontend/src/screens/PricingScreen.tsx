import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { getCreditPacks, createOrder, verifyPayment } from '../services/paymentApi'
import { useAuth } from '../context/AuthContext'
import { trackEvent } from '../utils/posthog'
import type { CreditPackInfo, CreditPackId } from '../types'

type CheckoutStep = 'idle' | 'creating_order' | 'opening_checkout' | 'verifying' | 'success' | 'error'

function formatInr(inr: number) {
  try {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(inr)
  } catch {
    return `₹${inr}`
  }
}

function getPackId(pack: CreditPackInfo): CreditPackId | null {
  const id = String(pack.id)
  if (id === 'starter' || id === 'pro' || id === 'enterprise') return id
  return null
}

async function loadRazorpayScript(): Promise<void> {
  if (typeof window === 'undefined') return
  if (window.Razorpay) return

  const existing = document.querySelector<HTMLScriptElement>('script[src="https://checkout.razorpay.com/v1/checkout.js"]')
  if (existing) {
    await new Promise<void>((resolve, reject) => {
      if (window.Razorpay) return resolve()
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Failed to load Razorpay script')))
    })
    return
  }

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Razorpay script'))
    document.body.appendChild(script)
  })
}

const PACK_FEATURES: Record<CreditPackId, string[]> = {
  starter: [
    '10 credits',
    'Studio-quality output',
    'No watermarks',
    'Valid for 7 days'
  ],
  pro: [
    '50 credits',
    'Studio-quality output',
    'No watermarks',
    'Valid for 30 days'
  ],
  enterprise: [
    '150 credits',
    'Studio-quality output',
    'No watermarks',
    'Valid for 60 days'
  ]
}

export default function PricingScreen() {
  const navigate = useNavigate()
  const { isAuthenticated, user, refreshCredits, loginWithKinde } = useAuth()
  const [packs, setPacks] = useState<CreditPackInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [checkoutStep, setCheckoutStep] = useState<CheckoutStep>('idle')
  const [checkoutPackId, setCheckoutPackId] = useState<CreditPackId | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    const fetchPacks = async () => {
      try {
        const res = await getCreditPacks()
        setPacks(res.packs ?? [])
        trackEvent('pricing_page_viewed')
      } catch (e: any) {
        setError(e?.response?.data?.detail?.message || e?.message || 'Failed to load pricing')
      } finally {
        setLoading(false)
      }
    }
    fetchPacks()
  }, [])

  const handleBuyPack = async (pack: CreditPackInfo) => {
    const packId = getPackId(pack)
    if (!packId) {
      setError('Invalid pack selected')
      return
    }

    if (!isAuthenticated) {
      // Trigger sign in flow
      trackEvent('pricing_signin_required', { pack_id: packId })
      loginWithKinde?.()
      return
    }

    setError(null)
    setSuccessMessage(null)
    setCheckoutPackId(packId)
    setCheckoutStep('creating_order')
    trackEvent('pricing_buy_clicked', { pack_id: packId })

    try {
      const order = await createOrder({ pack_id: packId })

      setCheckoutStep('opening_checkout')
      await loadRazorpayScript()
      if (!window.Razorpay) throw new Error('Razorpay SDK not available')

      const options: RazorpayOptions = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: 'MeeShip',
        description: `${pack.name} • ${pack.credits} credits`,
        order_id: order.order_id,
        prefill: {
          email: order.prefill?.email,
          name: order.prefill?.name ?? undefined,
        },
        notes: order.notes,
        theme: { color: '#ff007f' },
        handler: async (resp: RazorpayPaymentSuccessResponse) => {
          setCheckoutStep('verifying')
          trackEvent('pricing_payment_success', { pack_id: packId })

          try {
            await verifyPayment({
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            })
            
            await refreshCredits?.()
            setCheckoutStep('success')
            setSuccessMessage(`Successfully purchased ${pack.credits} credits!`)
            trackEvent('pricing_payment_verified', { pack_id: packId, credits: pack.credits })
          } catch (verifyErr: any) {
            setCheckoutStep('error')
            setError(verifyErr?.response?.data?.detail || 'Payment verification failed')
          }
        },
        modal: {
          ondismiss: () => {
            setCheckoutStep('idle')
            setCheckoutPackId(null)
            trackEvent('pricing_payment_dismissed', { pack_id: packId })
          },
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (e: any) {
      setCheckoutStep('error')
      setCheckoutPackId(null)
      setError(e?.response?.data?.detail || e?.message || 'Failed to start checkout')
    }
  }

  const formatExpiry = (expiryDate: string | null | undefined) => {
    if (!expiryDate) return null
    try {
      const date = new Date(expiryDate)
      const now = new Date()
      const daysLeft = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
      if (daysLeft <= 0) return 'Expired'
      if (daysLeft === 1) return 'Expires tomorrow'
      if (daysLeft <= 7) return `Expires in ${daysLeft} days`
      return `Expires ${date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`
    } catch {
      return null
    }
  }

  return (
    <Layout>
      <div className="mx-auto max-w-5xl px-4 pt-28 pb-16">
        {/* Back link */}
        <div className="mb-8">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-meesho transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl mb-4">
            Buy Credits
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Studio-quality images at just <span className="font-semibold text-meesho">₹0.33 per image</span>. No watermarks, no compromise.
          </p>
          <p className="mt-2 text-sm text-slate-500">
            1 credit = 1 product optimization → <span className="font-medium text-slate-700">30 shipping-ready images</span>
          </p>

          {/* Current balance */}
          {isAuthenticated && typeof user?.credits === 'number' && (
            <div className="mt-6 inline-flex items-center gap-3 rounded-full bg-slate-100 px-5 py-2.5 ring-1 ring-slate-200">
              <span className="text-sm text-slate-600">Current balance:</span>
              <span className="text-lg font-bold text-slate-900">{user.credits} credits</span>
              {user.creditsExpiresAt && (
                <span className="text-xs text-amber-600 font-medium">
                  • {formatExpiry(user.creditsExpiresAt)}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Success message */}
        {successMessage && (
          <div className="mb-8 rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-center">
            <p className="text-emerald-800 font-medium">{successMessage}</p>
            <button
              onClick={() => navigate('/')}
              className="mt-2 text-sm text-emerald-600 hover:text-emerald-700 underline"
            >
              Start optimizing images →
            </button>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-8 rounded-xl bg-red-50 border border-red-200 p-4 text-center">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-meesho border-t-transparent" />
          </div>
        ) : (
          /* Pricing cards */
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {packs.map((pack) => {
              const packId = getPackId(pack)
              const features = packId ? PACK_FEATURES[packId] : []
              const isPopular = packId === 'pro'
              const isProcessing = checkoutStep !== 'idle' && checkoutStep !== 'success' && checkoutStep !== 'error' && checkoutPackId === packId
              const isAnyProcessing = checkoutStep !== 'idle' && checkoutStep !== 'success' && checkoutStep !== 'error'

              return (
                <div
                  key={pack.id}
                  className={`relative rounded-2xl border-2 bg-white p-6 shadow-sm transition-all hover:shadow-md ${
                    isPopular ? 'border-meesho ring-2 ring-meesho/20' : 'border-slate-200'
                  }`}
                >
                  {/* Popular badge */}
                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="inline-block rounded-full bg-meesho px-4 py-1 text-xs font-bold text-white">
                        Most Popular
                      </span>
                    </div>
                  )}

                  {/* Pack info */}
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-slate-900 mb-1">{pack.name}</h3>
                    <div className="flex items-baseline justify-center gap-1">
                      <span className="text-4xl font-extrabold text-slate-900">{formatInr(pack.price_inr)}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-500">
                      ₹{(pack.price_inr / (pack.credits * 30)).toFixed(2)} per image
                    </p>
                  </div>

                  {/* Credits highlight */}
                  <div className="mb-6 rounded-xl bg-slate-50 p-4 text-center">
                    <span className="text-3xl font-bold text-meesho">{(pack.credits * 30).toLocaleString('en-IN')}</span>
                    <span className="ml-2 text-slate-600">images</span>
                  </div>

                  {/* Features */}
                  <ul className="mb-6 space-y-3">
                    {features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-slate-600">
                        <svg className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {/* Buy button */}
                  <button
                    onClick={() => handleBuyPack(pack)}
                    disabled={isAnyProcessing}
                    className={`w-full rounded-xl py-3 px-4 text-sm font-semibold transition-all ${
                      isPopular
                        ? 'bg-meesho text-white hover:bg-meesho/90 disabled:bg-meesho/50'
                        : 'bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-400'
                    } disabled:cursor-not-allowed`}
                  >
                    {isProcessing ? (
                      <span className="inline-flex items-center gap-2">
                        <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        {checkoutStep === 'creating_order' && 'Creating order...'}
                        {checkoutStep === 'opening_checkout' && 'Opening Razorpay...'}
                        {checkoutStep === 'verifying' && 'Verifying payment...'}
                      </span>
                    ) : isAuthenticated ? (
                      'Buy Now'
                    ) : (
                      'Sign in to Buy'
                    )}
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Trust badges */}
        <div className="mt-12 text-center">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-meesho" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
              Studio-quality AI
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              No watermarks
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Instant delivery
            </div>
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Secure Razorpay
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
