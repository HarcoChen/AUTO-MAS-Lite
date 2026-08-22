import { OpenAPI } from '@/api/core/OpenAPI'
import { request } from '@/api/core/request'

export interface MaaEndUpdaterDebugRequest {
  scriptId: string
  updaterPath?: string
  currentVersion: string
  platform?: string
  source: 'auto' | 'mirrorchyan' | 'github'
  waitPid?: number
  relaunch?: string
  timeoutSeconds?: number
}

export interface MaaEndUpdaterDebugResponse {
  code?: number
  status?: string
  message?: string
  data?: {
    root?: string
    spec?: Record<string, unknown>
    returncode?: number
    events?: Array<Record<string, unknown>>
    stdout?: string
    stderr?: string
    resource_reloaded?: boolean
  }
}

export const maaEndUpdaterDebugApi = {
  update: (body: MaaEndUpdaterDebugRequest) =>
    request<MaaEndUpdaterDebugResponse>(OpenAPI, {
      method: 'POST',
      url: '/api/debug/maaend-update',
      body,
      mediaType: 'application/json',
    }),
}
