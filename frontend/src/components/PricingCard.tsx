interface PricingCardProps {
  onUpgrade: () => void
}

export default function PricingCard({ onUpgrade }: PricingCardProps) {
  return (
    <div className="fixed bottom-0 inset-x-0 bg-gradient-to-t from-white via-white to-transparent pt-8 pb-6">
      <div className="mx-auto max-w-5xl px-4">
        <div className="rounded-2xl bg-gradient-to-r from-meesho to-meesho/80 p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-lg font-bold">Upgrade to Pro</div>
              <div className="mt-1 text-sm text-white/80">
                Get unlimited image generations and priority processing
              </div>
            </div>
            <button
              type="button"
              onClick={onUpgrade}
              className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-meesho hover:bg-white/90 transition-colors"
            >
              Upgrade Now
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}