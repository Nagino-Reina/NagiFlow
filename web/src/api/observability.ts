/**
 * api/observability.ts
 *
 * System resources, service health, and token-usage summary (docs/05 §4.7, docs/12).
 */

import { http } from './http'
import type { ServiceStatus, SystemResources, UsageSummary } from './types'

export const observabilityApi = {
  resources: () => http.get<SystemResources>('/system/resources'),
  services: () => http.get<{ services: ServiceStatus[] }>('/system/services'),
  usageSummary: () => http.get<UsageSummary>('/usage:summary'),
}
