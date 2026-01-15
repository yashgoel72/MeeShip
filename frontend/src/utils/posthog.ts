import posthog from 'posthog-js'

let initialized = false

export function initPostHog() {
  if (initialized) return
  const key = import.meta.env.VITE_POSTHOG_KEY as string | undefined
  const host = (import.meta.env.VITE_POSTHOG_HOST as string | undefined) || 'https://app.posthog.com'
  if (!key) return

  posthog.init(key, {
    api_host: host,
    capture_pageview: false,
    persistence: 'localStorage',
  })
  initialized = true
}

export function trackEvent(event: string, properties?: Record<string, any>) {
  if (!initialized) initPostHog()
  try {
    posthog.capture(event, properties)
  } catch {
    // analytics must never break UX
  }
}
