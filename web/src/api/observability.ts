/**
 * api/observability.ts
 *
 * Service health for the Settings → Providers table (docs/05 §4.7). Live resources + usage are
 * pushed over the system-status WebSocket (see `realtime/systemClient`), not polled here.
 */

import type { ServiceStatus } from './types'
import { http } from './http'

export const observabilityApi = {
  services: () => http.get<{ services: ServiceStatus[] }>('/system/services'),
}
