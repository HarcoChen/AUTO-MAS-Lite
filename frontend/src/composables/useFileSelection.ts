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

// ===== API 客户端 =====

const getBaseUrl = (): string => {
  if (window.electronAPI?.getApiEndpoint) {
    return window.electronAPI.getApiEndpoint('rest')
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

export function useFileSelection() {
  // ===== 文件选择 =====

  /**
   * 选择单个文件
   * Web 模式: 使用 <input type="file"> 元素，返回文件名
   * 注意：Web 中无法获取完整路径，返回的是文件名
   */
  const selectFile = async (options: FileSelectOptions = {}): Promise<string | null> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = false

      // 设置文件过滤器
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
        logger.info(`已选择文件: ${file.name} (${file.size} bytes)`)
      }

      input.click()
    })
  }

  // ===== 文件夹选择 =====

  /**
   * 选择文件夹（Web 模式使用 webkitdirectory）
   * 返回用户选择的完整路径（如果浏览器允许），否则只返回文件夹名
   */
  const selectFolder = async (): Promise<string | null> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = false
      input.webkitdirectory = true
      input.mozdirectory = true
      input.directory = true

      input.onchange = (e) => {
        const files = (e.target as HTMLInputElement).files
        if (!files || files.length === 0) {
          resolve(null)
          return
        }

        // 尝试获取完整路径（部分浏览器可能只返回文件名）
        const file = files[0]
        // webkitRelativePath 包含相对于选择文件夹的路径
        const path = file.webkitRelativePath || file.name
        const folderPath = path.split('/')[0]

        resolve(folderPath)
        logger.info(`已选择文件夹: ${folderPath}`)
      }

      input.click()
    })
  }

  /**
   * 选择多个文件
   */
  const selectFiles = async (options: FileSelectOptions = {}): Promise<string[]> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = true

      // 设置文件过滤器
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
        logger.info(`已选择 ${fileNames.length} 个文件`)
      }

      input.click()
    })
  }

  // ===== 路径输入 =====

  /**
   * 验证用户输入的路径
   */
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

    // 调用后端 API 验证路径
    return await validatePath(path)
  }

  /**
   * 读取用户输入路径的内容
   */
  const readInputPath = async (path: string): Promise<PathReadResult> => {
    return await readPath(path)
  }

  // ===== 常用路径 =====

  /**
   * 获取常用系统路径列表
   */
  const fetchSystemPaths = async (): Promise<SystemPathItem[]> => {
    return await getSystemPaths()
  }

  return {
    // 文件选择
    selectFile,
    selectFolder,
    selectFiles,
    // 路径验证和读取
    validateInputPath,
    readInputPath,
    // 系统路径
    fetchSystemPaths,
    // 工具函数
    getApiBaseUrl,
  }
}
