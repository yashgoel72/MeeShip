import { useState } from 'react'
import PaymentModal from './PaymentModal'
import { useAuth } from '../context/AuthContext'

interface UpgradeBannerProps {
  credits?: number
  expiresAt?: string | null
}

export default function UpgradeBanner({ credits, expiresAt }: UpgradeBannerProps) {
  const [paymentOpen, setPaymentOpen] = useState(false)
  const { refreshCredits } = useAuth()

  // Don't show banner if credits haven't been loaded yet (undefined)
  // or if user has plenty of credits (> 3) and not expiring soon
  if (credits === undefined) {
    return null
  }

  // Calculate days remaining
  const daysRemaining = expiresAt
    ? Math.max(0, Math.ceil((new Date(expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
    : null

  const isExpiringSoon = daysRemaining !== null && daysRemaining <= 3
  const isExpired = daysRemaining !== null && daysRemaining === 0
  const hasLowCredits = credits > 0 && credits <= 3

  // Don't show if user has plenty of credits and time
  if (credits > 3 && !isExpiringSoon) {
    return null
  }

  let message = ''
  let urgency: 'low' | 'medium' | 'high' = 'low'

  if (credits === 0 || isExpired) {
    message = 'You have no credits remaining. Buy a pack to continue saving on shipping.'
    urgency = 'high'
  } else if (hasLowCredits && isExpiringSoon) {
    message = `Only ${credits} credits left, expiring in ${daysRemaining} day${daysRemaining === 1 ? '' : 's'}!`
    urgency = 'high'
  } else if (hasLowCredits) {
    message = `You have ${credits} credits remaining. Top up to keep saving!`
    urgency = 'medium'
  } else if (isExpiringSoon) {
    message = `Your credits expire in ${daysRemaining} day${daysRemaining === 1 ? '' : 's'}. Use them or buy more!`
    urgency = 'medium'
  }

  if (!message) return null

  const bgColor = {
    low: 'bg-blue-50 ring-blue-200',
    medium: 'bg-amber-50 ring-amber-200',
    high: 'bg-rose-50 ring-rose-200',
  }[urgency]

  const textColor = {
    low: 'text-blue-800',
    medium: 'text-amber-800',
    high: 'text-rose-800',
  }[urgency]

  const buttonColor = {
    low: 'bg-blue-600 hover:bg-blue-700',
    medium: 'bg-amber-600 hover:bg-amber-700',
    high: 'bg-rose-600 hover:bg-rose-700',
  }[urgency]

  return (
    <>
      <div className={`mx-auto w-full max-w-2xl rounded-2xl px-4 py-3 ring-1 ${bgColor}`}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className={`text-sm font-medium ${textColor}`}>
            <span className="mr-2">💳</span>
            {message}
          </div>
          <button
            type="button"
            onClick={() => setPaymentOpen(true)}
            className={`shrink-0 rounded-xl px-4 py-2 text-sm font-semibold text-white transition-colors ${buttonColor}`}
          >
            Buy Credits
          </button>
        </div>

        {/* Pricing hint */}
        <div className={`mt-2 text-xs ${textColor} opacity-80`}>
          Starting at ₹99 — save on thousands of orders
        </div>
      </div>

      <PaymentModal 
        open={paymentOpen} 
        onClose={() => setPaymentOpen(false)} 
        onSuccess={refreshCredits}
      />
    </>
  )
}
