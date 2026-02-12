import { message } from 'ant-design-vue'
import { createLogger } from '@/utils/logger'
import { OpenAPI } from '@/api'

const logger = createLogger('文件选择')

// ===== 类型定义 =====

export interface FileSelectOptions {
  filters?: Array<{ name: string; extensions: string[] }>
  multiple?: boolean
}

export interface PathValidateResult {
  valid: boolean
  exists: boolean
  readable: boolean
  isDir: boolean
  isFile: boolean
  normalizedPath: string
  error?: string
}

export interface PathReadResult {
  exists: boolean
  isDir: boolean
  isFile: boolean
  content?: string
  files?: Array<{ name: string; path: string; isDir: boolean; isFile: boolean }>
  error?: string
}

export interface SystemPathItem {
  name: string
  path: string
}

// ===== 检测是否为真正的 Electron 环境 =====
const hasRealElectronAPI = (): boolean => {
  return (
    typeof window !== 'undefined' &&
    (window as any).electronAPI !== undefined &&
    'installPython' in (window as any).electronAPI
  )
}

const isElectron = hasRealElectronAPI()

// ===== 检测是否支持 File System Access API =====
const supportsFileSystemAccess = (): boolean => {
  return 'showOpenFilePicker' in window || 'showDirectoryPicker' in window
}

// ===== API 客户端 =====

const getBaseUrl = (): string => {
  if (window.electronAPI?.getApiEndpoint) {
    return window.electronAPI.getApiEndpoint('rest') as string
  }
  return OpenAPI.BASE || 'http://localhost:36163'
}

/**
 * 验证路径有效性
 */
export async function validatePath(path: string): Promise<PathValidateResult> {
  try {
    const response = await fetch(`${getBaseUrl()}/api/path/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, check_exists: true, check_readable: true }),
    })
    const data = await response.json()
    return {
      valid: data.valid,
      exists: data.exists,
      readable: data.readable,
      isDir: data.is_dir,
      isFile: data.is_file,
      normalizedPath: data.normalized_path,
      error: data.error,
    }
  } catch (error) {
    logger.error(`验证路径失败: ${path}`, error)
    return {
      valid: false,
      exists: false,
      readable: false,
      isDir: false,
      isFile: false,
      normalizedPath: path,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * 读取路径内容（文件内容或目录列表）
 */
export async function readPath(path: string, encoding = 'utf-8'): Promise<PathReadResult> {
  try {
    const response = await fetch(`${getBaseUrl()}/api/path/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, encoding }),
    })
    const data = await response.json()
    return {
      exists: data.exists,
      isDir: data.is_dir,
      isFile: data.is_file,
      content: data.content,
      files: data.files,
      error: data.error,
    }
  } catch (error) {
    logger.error(`读取路径失败: ${path}`, error)
    return {
      exists: false,
      isDir: false,
      isFile: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * 获取常用系统路径列表
 */
export async function getSystemPaths(): Promise<SystemPathItem[]> {
  try {
    const response = await fetch(`${getBaseUrl()}/api/path/system`)
    const data = await response.json()
    return data.paths || []
  } catch (error) {
    logger.error('获取系统路径失败', error)
    return []
  }
}

/**
 * 获取 API BASE URL
 */
export function getApiBaseUrl(): string {
  return getBaseUrl()
}

/**
 * 检查是否是 Web 模式
 */
export function isWebMode(): boolean {
  return !isElectron
}

/**
 * 检查是否支持获取完整路径
 */
export function canGetFullPath(): boolean {
  return isElectron || supportsFileSystemAccess()
}

/**
 * 设置拖拽事件处理器（Web 模式下获取完整路径的最佳方式）
 */
export function setupDragDropHandler(
  container: HTMLElement,
  onDrop: (path: string, isFile: boolean) => void
): () => void {
  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    container.classList.add('drag-over')
  }

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    container.classList.remove('drag-over')
  }

  const handleDrop = async (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    container.classList.remove('drag-over')

    const items = e.dataTransfer?.items
    if (!items) return

    for (const item of items) {
      if (item.kind === 'file') {
        const file = item.getAsFile()
        if (file) {
          // 在 Chromium 拖拽中，可以获取完整路径
          const fileAny = file as any
          const path = fileAny.path || fileAny.webkitRelativePath || file.name
          const isDir = !path.includes('.') || fileAny.isDirectory

          logger.info(`拖拽获取路径: ${path}`)
          onDrop(path, !isDir && !path.endsWith('/'))
          return
        }
      }
    }
  }

  container.addEventListener('dragover', handleDragOver)
  container.addEventListener('dragleave', handleDragLeave)
  container.addEventListener('drop', handleDrop)

  return () => {
    container.removeEventListener('dragover', handleDragOver)
    container.removeEventListener('dragleave', handleDragLeave)
    container.removeEventListener('drop', handleDrop)
  }
}

export function useFileSelection() {
  // ===== Electron 模式 =====

  /**
   * Electron 模式选择单个文件
   */
  const electronSelectFile = async (options: FileSelectOptions = {}): Promise<string | null> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = false

      if (options.filters && options.filters.length > 0) {
        input.accept = options.filters
          .flatMap((f) => f.extensions.map((e) => `.${e}`))
          .join(',')
      }

      input.onchange = (e) => {
        const files = (e.target as HTMLInputElement).files
        if (!files || files.length === 0) {
          resolve(null)
          return
        }
        const file = files[0]
        resolve(file.name)
        logger.info(`已选择文件: ${file.name}`)
      }

      input.click()
    })
  }

  /**
   * Electron 模式选择文件夹
   */
  const electronSelectFolder = async (): Promise<string | null> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = false
      ;(input as any).webkitdirectory = true

      input.onchange = (e) => {
        const files = (e.target as HTMLInputElement).files
        if (!files || files.length === 0) {
          resolve(null)
          return
        }
        const file = files[0]
        const path = (file as any).webkitRelativePath || file.name
        const folderPath = path.split('/')[0]
        resolve(folderPath)
        logger.info(`已选择文件夹: ${folderPath}`)
      }

      input.click()
    })
  }

  // ===== Web 模式：File System Access API =====

  /**
   * 使用 File System Access API 选择文件（Chrome/Edge 支持）
   */
  const webkitSelectFile = async (options: FileSelectOptions = {}): Promise<string | null> => {
    if (!supportsFileSystemAccess()) {
      return null
    }

    try {
      const fileTypes = options.filters?.map((f) => ({
        description: f.name,
        accept: { 'application/octet-stream': f.extensions.map((e) => `.${e}`) },
      })) || [{ description: '所有文件', accept: { 'application/octet-stream': ['*'] } }]

      const [handle] = await (window as any).showOpenFilePicker({
        types: fileTypes,
        multiple: false,
      })
      const file = await handle.getFile()
      // 尝试获取完整路径
      const path = (file as any).path || file.name
      logger.info(`已选择文件: ${path}`)
      return path
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return null
      }
      logger.error('文件选择失败', error)
      return null
    }
  }

  /**
   * 使用 File System Access API 选择文件夹（Chrome/Edge 支持）
   */
  const webkitSelectFolder = async (): Promise<string | null> => {
    if (!supportsFileSystemAccess()) {
      return null
    }

    try {
      const handle = await (window as any).showDirectoryPicker()
      // 注意：showDirectoryPicker 不直接返回路径，需要用户授权
      // 尝试获取路径
      const path = (handle as any).name || (handle as any).path || ''
      logger.info(`已选择文件夹: ${path}`)
      return path || null
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return null
      }
      logger.error('文件夹选择失败', error)
      return null
    }
  }

  // ===== 统一接口 =====

  /**
   * 选择单个文件
   * 优先级：Electron IPC > File System Access API > input
   */
  const selectFile = async (options: FileSelectOptions = {}): Promise<string | null> => {
    if (isElectron) {
      return await electronSelectFile(options)
    } else if (supportsFileSystemAccess()) {
      return await webkitSelectFile(options)
    } else {
      // 回退到 input，但只能获取文件名
      return await electronSelectFile(options)
    }
  }

  /**
   * 选择文件夹
   * 推荐：使用拖拽获取完整路径
   */
  const selectFolder = async (): Promise<string | null> => {
    if (isElectron) {
      return await electronSelectFolder()
    } else if (supportsFileSystemAccess()) {
      return await webkitSelectFolder()
    } else {
      // 提示用户使用拖拽
      message.info('Web 模式：请将文件夹拖拽到浏览器窗口以获取完整路径')
      logger.info('Web 模式：等待拖拽获取路径')
      return null
    }
  }

  /**
   * 选择多个文件
   */
  const selectFiles = async (options: FileSelectOptions = {}): Promise<string[]> => {
    if (isElectron) {
      return new Promise((resolve) => {
        const input = document.createElement('input')
        input.type = 'file'
        input.multiple = true

        if (options.filters && options.filters.length > 0) {
          input.accept = options.filters
            .flatMap((f) => f.extensions.map((e) => `.${e}`))
            .join(',')
        }

        input.onchange = (e) => {
          const files = (e.target as HTMLInputElement).files
          if (!files || files.length === 0) {
            resolve([])
            return
          }
          const fileNames = Array.from(files).map((f) => f.name)
          resolve(fileNames)
        }

        input.click()
      })
    } else {
      message.warning('Web 模式：请拖拽文件到浏览器')
      return []
    }
  }

  // ===== 路径验证和读取 =====

  const validateInputPath = async (path: string): Promise<PathValidateResult> => {
    if (!path || path.trim() === '') {
      return {
        valid: false,
        exists: false,
        readable: false,
        isDir: false,
        isFile: false,
        normalizedPath: '',
        error: '路径不能为空',
      }
    }
    return await validatePath(path)
  }

  const readInputPath = async (path: string): Promise<PathReadResult> => {
    return await readPath(path)
  }

  // ===== 常用路径 =====

  const fetchSystemPaths = async (): Promise<SystemPathItem[]> => {
    return await getSystemPaths()
  }

  return {
    selectFile,
    selectFolder,
    selectFiles,
    validateInputPath,
    readInputPath,
    fetchSystemPaths,
    getApiBaseUrl,
    isWebMode,
    canGetFullPath,
    setupDragDropHandler,
  }
}
