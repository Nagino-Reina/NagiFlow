/**
 * api/media.ts
 *
 * Media asset access (docs/05 §4.6). The SPA authenticates with a localStorage bearer token,
 * which a native `<audio src>` request cannot carry — so fetch the bytes with the token and
 * play them from an object URL instead.
 */

import { getToken } from './session'

const BASE = '/api/v1'

export const mediaApi = {
  /** Download an asset with the session bearer token and return a playable object URL.
      Caller is responsible for `URL.revokeObjectURL` when done. */
  async fetchObjectUrl (id: string): Promise<string> {
    const token = getToken()
    const res = await fetch(`${BASE}/media/${id}:download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) {
      throw new Error(`media download failed (${res.status})`)
    }
    return URL.createObjectURL(await res.blob())
  },
}
