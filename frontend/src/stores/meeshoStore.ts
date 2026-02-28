/**
 * Centralized Meesho account state store.
 *
 * Single source of truth for:
 *  - whether the user has linked a Meesho account
 *  - whether the current session token is still valid
 *  - supplier ID and linked-at timestamp
 *
 * All components read from this store instead of making their own
 * /api/meesho/status calls, eliminating stale-state bugs.
 */

import { create } from 'zustand'
import { getMeeshoStatus, validateMeeshoSession } from '../services/meeshoApi'

export type MeeshoState = {
  /** null = not yet checked, true/false = known */
  linked: boolean | null
  /** null = not yet checked */
  sessionValid: boolean | null
  supplierId: string | null
  linkedAt: string | null
  /** True while a fetch is in-flight (prevents duplicate calls) */
  loading: boolean
  /** Session-expired message from validation */
  sessionExpiredMessage: string | null

  // ── Actions ──────────────────────────────────────────────
  /** Fetch status + validate session from the backend. Safe to call many times — deduplicates. */
  fetchStatus: () => Promise<void>
  /** Mark as linked (call after successful link) */
  markLinked: (supplierId?: string) => void
  /** Mark as unlinked (call after unlink) */
  markUnlinked: () => void
  /** Mark session expired (call when streaming or API returns SESSION_EXPIRED) */
  markSessionExpired: (message?: string) => void
  /** Reset everything (call on logout) */
  reset: () => void
}

const initialState = {
  linked: null as boolean | null,
  sessionValid: null as boolean | null,
  supplierId: null as string | null,
  linkedAt: null as string | null,
  loading: false,
  sessionExpiredMessage: null as string | null,
}

/** In-flight promise — prevents concurrent fetches */
let _inflightFetch: Promise<void> | null = null

export const useMeeshoStore = create<MeeshoState>((set, _get) => ({
  ...initialState,

  fetchStatus: async () => {
    // Deduplicate: if a fetch is already in-flight, wait for it instead
    if (_inflightFetch) {
      await _inflightFetch
      return
    }

    set({ loading: true })

    const doFetch = async () => {
      try {
        const status = await getMeeshoStatus()
        set({
          linked: status.linked,
          supplierId: status.supplier_id,
          linkedAt: status.linked_at,
        })

        if (status.linked) {
          try {
            const validation = await validateMeeshoSession()
            if (validation.valid) {
              set({ sessionValid: true, sessionExpiredMessage: null })
            } else {
              set({
                sessionValid: false,
                sessionExpiredMessage:
                  validation.message || 'Your Meesho session has expired. Please re-link your account.',
              })
            }
          } catch {
            // Validation call failed — assume valid to avoid false negatives
            set({ sessionValid: true, sessionExpiredMessage: null })
          }
        } else {
          set({ sessionValid: null, sessionExpiredMessage: null })
        }
      } catch {
        set({ linked: false, sessionValid: null })
      } finally {
        set({ loading: false })
        _inflightFetch = null
      }
    }

    _inflightFetch = doFetch()
    await _inflightFetch
  },

  markLinked: (supplierId?: string) => {
    set({
      linked: true,
      sessionValid: true,
      sessionExpiredMessage: null,
      ...(supplierId ? { supplierId } : {}),
    })
  },

  markUnlinked: () => {
    set({
      linked: false,
      sessionValid: null,
      supplierId: null,
      linkedAt: null,
      sessionExpiredMessage: null,
    })
  },

  markSessionExpired: (message?: string) => {
    set({
      sessionValid: false,
      sessionExpiredMessage: message || 'Your Meesho session has expired. Please re-link your account.',
    })
  },

  reset: () => {
    _inflightFetch = null
    set(initialState)
  },
}))
