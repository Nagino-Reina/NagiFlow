/**
 * stores/auth.ts
 *
 * Session/principal state (docs/03 §5, docs/05 §2). A guest session is auto-issued on
 * first contact; a local-account login upgrades capabilities. The client never decides
 * access — it reflects the server-resolved principal and gates UI affordances by `kind`.
 */

import type { Principal } from '@/api/types'
import { defineStore } from 'pinia'
import { authApi, type LoginBody, type RegisterBody } from '@/api/auth'
import { getToken, setToken } from '@/api/session'

type Status = 'idle' | 'loading' | 'ready' | 'error'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    principal: null as Principal | null,
    status: 'idle' as Status,
  }),
  getters: {
    isUser: state => state.principal?.kind === 'user',
    isGuest: state => state.principal?.kind === 'guest',
  },
  actions: {
    /** Issue a guest session and load the principal. */
    async startGuest () {
      const { token } = await authApi.guest()
      setToken(token)
      this.principal = await authApi.me()
    },
    /** Resolve the current principal: reuse a stored token, else issue a guest session. */
    async ensureSession () {
      this.status = 'loading'
      try {
        if (getToken()) {
          this.principal = await authApi.me()
        } else {
          await this.startGuest()
        }
        this.status = 'ready'
      } catch {
        // Stale/invalid token → fall back to a fresh guest session.
        setToken(null)
        try {
          await this.startGuest()
          this.status = 'ready'
        } catch {
          this.status = 'error'
        }
      }
    },
    async login (body: LoginBody) {
      const { token } = await authApi.login(body)
      setToken(token)
      this.principal = await authApi.me()
      this.status = 'ready'
    },
    /** Register creates the account, then logs in to start the session. */
    async register (body: RegisterBody) {
      await authApi.register(body)
      await this.login({ username: body.username, password: body.password })
    },
    async logout () {
      try {
        await authApi.logout()
      } finally {
        setToken(null)
        this.principal = null
        await this.ensureSession()
      }
    },
  },
})
