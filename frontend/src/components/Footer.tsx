import { Link } from 'react-router-dom'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-slate-200 bg-slate-900 text-white">
      <div className="mx-auto max-w-6xl px-4 py-12">
        {/* Trust badges row */}
        <div className="mb-10 flex flex-wrap items-center justify-center gap-3 rounded-2xl bg-white/5 px-6 py-4 ring-1 ring-white/10">
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            256-bit Encrypted
          </div>
          <span className="text-slate-700">•</span>
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
            <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
            Passwords Never Stored
          </div>
          <span className="text-slate-700">•</span>
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
            <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
            </svg>
            Razorpay Secured Payments
          </div>
          <span className="text-slate-700">•</span>
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
            🇮🇳 Made in India
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="col-span-1 sm:col-span-2 lg:col-span-1">
            <div className="text-lg font-extrabold tracking-tight font-display">
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
