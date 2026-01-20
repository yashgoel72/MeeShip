import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import LandingScreen from './screens/LandingScreen.tsx'
import ProcessingScreen from './screens/ProcessingScreen.tsx'
import ResultScreen from './screens/ResultScreen.tsx'
import TermsPage from './screens/TermsPage.tsx'
import PrivacyPage from './screens/PrivacyPage.tsx'
import RefundPage from './screens/RefundPage.tsx'
import ContactPage from './screens/ContactPage.tsx'
import PricingScreen from './screens/PricingScreen.tsx'
import { useAppStore } from './stores/appStore.ts'

// Main app flow component (landing -> processing -> result)
function MainFlow() {
  const screen = useAppStore((s) => s.screen)

  return (
    <div className="min-h-screen bg-offwhite text-slate-900">
      <AnimatePresence mode="wait">
        {screen === 'landing' && (
          <motion.div
            key="landing"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <LandingScreen />
          </motion.div>
        )}

        {screen === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <ProcessingScreen />
          </motion.div>
        )}

        {screen === 'result' && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <ResultScreen />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainFlow />} />
        <Route path="/pricing" element={<PricingScreen />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/refund" element={<RefundPage />} />
        <Route path="/contact" element={<ContactPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App