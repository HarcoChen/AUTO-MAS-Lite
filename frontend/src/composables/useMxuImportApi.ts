import { ref } from 'vue'
import type { MaaFWTaskSnapshot } from '@/types/script'

const logger = window.electronAPI.getLogger('MXU配置导入')

export interface MxuInstanceSummary {
  id: string
  name: string
  controller: string
  resource: string
  task_count: number
  enabled_task_count: number
}

export interface MxuImportPreview {
  config_path: string
  selected_instance_id: string
  instances: MxuInstanceSummary[]
  controller: string
  resource: string
  snapshot: MaaFWTaskSnapshot
  warnings: string[]
}

interface MxuImportResponse {
  code?: number
  message?: string
  data?: MxuImportPreview
}

interface MxuImportStatusResponse {
  code?: number
  data?: {
    available?: boolean
  }
}

export function useMxuImportApi() {
  const loading = ref(false)

  const checkMxuImportAvailable = async (): Promise<boolean> => {
    try {
      const response = (await window.pluginAPI.call(
        '/plugin/mxu/import/status'
      )) as MxuImportStatusResponse
      return response.code === 200 && response.data?.available === true
    } catch {
      return false
    }
  }

  const previewMxuConfig = async (
    projectPath: string,
    instanceId?: string
  ): Promise<MxuImportPreview> => {
    loading.value = true
    try {
      const response = (await window.pluginAPI.call('/plugin/mxu/import/preview', {
        projectPath,
        instanceId: instanceId || undefined,
      })) as MxuImportResponse
      if (response.code !== 200 || !response.data) {
        throw new Error(response.message || 'MXU 配置解析失败')
      }
      return response.data
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'MXU 配置解析失败'
      logger.error(`MXU 配置解析失败: ${errorMessage}`)
      throw new Error(errorMessage)
    } finally {
      loading.value = false
    }
  }

  return { loading, checkMxuImportAvailable, previewMxuConfig }
}
