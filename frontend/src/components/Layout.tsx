import { ReactNode } from 'react'
import Header from './Header'
import Footer from './Footer'

interface LayoutProps {
  children: ReactNode
  onSignIn?: () => void
  hideFooter?: boolean
}

export default function Layout({ children, onSignIn, hideFooter = false }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50 via-white to-blue-50/30">
      <Header onSignIn={onSignIn} />
      <main className="flex-1">
        {children}
      </main>
      {!hideFooter && <Footer />}
    </div>
  )
}
