import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useScroll } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useMeeshoStore } from '../stores/meeshoStore'
import MeeshoLinkModal from './MeeshoLinkModal'

interface HeaderProps {
  onSignIn?: () => void
}

export default function Header({ onSignIn }: HeaderProps) {
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()
  const location = useLocation()
  const meeshoLinked = useMeeshoStore((s) => s.linked)
  const sessionValid = useMeeshoStore((s) => s.sessionValid)
  const fetchMeeshoStatus = useMeeshoStore((s) => s.fetchStatus)
  const resetMeesho = useMeeshoStore((s) => s.reset)
  const [showMeeshoModal, setShowMeeshoModal] = useState(false)

  const isHomePage = location.pathname === '/'

  useEffect(() => {
    const unsub = scrollY.on('change', (v) => setScrolled(v > 8))
    return () => unsub()
  }, [scrollY])

  // Fetch Meesho status from shared store when authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      resetMeesho()
      return
    }
    fetchMeeshoStatus()
  }, [isAuthenticated, fetchMeeshoStatus, resetMeesho])

  return (
    <header className={
      'fixed inset-x-0 top-0 z-40 transition-colors ' +
      (scrolled ? 'bg-white/90 backdrop-blur ring-1 ring-slate-200' : 'bg-transparent')
    }>
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link to="/" className="flex items-center gap-3">
          <div>
            <div className="text-sm font-extrabold tracking-tight text-slate-900">
              MeeShip
              <span className="ml-2 inline-block h-0.5 w-8 align-middle bg-amber-500" />
            </div>
            <div className="hidden text-[10px] font-medium text-slate-500 sm:block">
              Meesho का Smart Shipping Tool
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 sm:flex">
          <Link 
            to="/" 
            className={`text-sm font-medium transition-colors ${
              isHomePage ? 'text-meesho' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Home
          </Link>
          <Link 
            to="/contact" 
            className={`text-sm font-medium transition-colors ${
              location.pathname === '/contact' ? 'text-meesho' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
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
                  onClick={() => setShowMeeshoModal(true)}
                  className={`hidden items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 transition-colors sm:flex ${
                    meeshoLinked && sessionValid !== false
                      ? 'bg-pink-50 text-pink-700 ring-pink-200 hover:bg-pink-100'
                      : meeshoLinked && sessionValid === false
                        ? 'bg-amber-50 text-amber-700 ring-amber-200 hover:bg-amber-100'
                        : 'bg-gray-50 text-gray-600 ring-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  {meeshoLinked && sessionValid !== false
                    ? 'Meesho ✓'
                    : meeshoLinked && sessionValid === false
                      ? 'Session Expired'
                      : 'Link Meesho'}
                </button>
              )}
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

      {/* Meesho Link Modal */}
      <MeeshoLinkModal
        open={showMeeshoModal}
        onClose={() => setShowMeeshoModal(false)}
        onSuccess={() => useMeeshoStore.getState().markLinked()}
      />
    </header>
  )
}
