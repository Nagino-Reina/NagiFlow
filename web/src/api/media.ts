/**
 * api/media.ts
 *
 * Media asset access (docs/05 §4.6). The download URL is used directly as an `<audio>` src;
 * it authenticates via the session cookie (same-origin), so no Authorization header is needed.
 */

const BASE = '/api/v1'

export const mediaApi = {
  downloadUrl: (id: string) => `${BASE}/media/${id}:download`,
}
