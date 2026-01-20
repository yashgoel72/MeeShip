import { Link } from 'react-router-dom'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-slate-200 bg-slate-900 text-white">
      <div className="mx-auto max-w-6xl px-4 py-12">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="col-span-1 sm:col-span-2 lg:col-span-1">
            <div className="text-lg font-extrabold tracking-tight">
              MeeShip
              <span className="ml-2 inline-block h-0.5 w-8 align-middle bg-amber-500" />
            </div>
            <p className="mt-1 text-sm font-medium text-amber-400">
              Meesho का Smart Shipping Tool
            </p>
            <p className="mt-3 text-sm text-slate-400">
              AI-powered shipping-optimized product photos for Meesho sellers. 
              Save ₹10-20 on every order.
            </p>
            <div className="mt-4 flex items-center gap-2">
              <div className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-300">
                🔒 Secured by Razorpay
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <div className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Quick Links
            </div>
            <ul className="mt-4 space-y-3">
              <li>
                <Link to="/" className="text-sm text-slate-300 hover:text-white transition-colors">
                  Home
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <div className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Legal
            </div>
            <ul className="mt-4 space-y-3">
              <li>
                <Link to="/terms" className="text-sm text-slate-300 hover:text-white transition-colors">
                  Terms & Conditions
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-sm text-slate-300 hover:text-white transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/refund" className="text-sm text-slate-300 hover:text-white transition-colors">
                  Refund Policy
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <div className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Contact Us
            </div>
            <ul className="mt-4 space-y-3">
              <li>
                <Link to="/contact" className="text-sm text-slate-300 hover:text-white transition-colors">
                  Contact Page
                </Link>
              </li>
              <li>
                <a 
                  href="mailto:meeship.seller@gmail.com" 
                  className="text-sm text-slate-300 hover:text-white transition-colors"
                >
                  meeship.seller@gmail.com
                </a>
              </li>
              <li className="text-sm text-slate-400">
                Mon-Sat: 10 AM - 6 PM IST
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-10 border-t border-slate-800 pt-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-slate-400">
              © {currentYear} MeeShip. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <span className="text-xs text-slate-500">
                Payments processed securely by Razorpay
              </span>
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5 text-slate-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                <span className="text-xs text-slate-500">Made in India 🇮🇳</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
