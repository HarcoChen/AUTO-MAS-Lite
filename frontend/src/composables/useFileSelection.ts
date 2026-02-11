import { message } from 'ant-design-vue'
import { createLogger } from '@/utils/logger'

const logger = createLogger('文件选择')

interface FileSelectOptions {
  filters?: Array<{ name: string; extensions: string[] }>
  multiple?: boolean
}

export function useFileSelection() {
  /**
   * 选择文件
   * Web 模式: 使用 <input type="file"> 元素
   */
  const selectFile = async (options: FileSelectOptions = {}): Promise<string | null> => {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = options.multiple ?? false

      // 设置文件过滤器
      if (options.filters && options.filters.length > 0) {
        input.accept = options.filters
          .flatMap(f => f.extensions.map(e => `.${e}`))
          .join(',')
      }

      input.onchange = (e) => {
        const files = (e.target as HTMLInputElement).files
        if (!files || files.length === 0) {
          resolve(null)
          return
        }

        const file = files[0]
        // 返回文件对象，调用方可以进一步处理
        resolve(file.name)
        logger.info(`已选择文件: ${file.name} (${file.size} bytes)`)
      }

      input.click()
    })
  }

  /**
   * 选择文件夹
   * Web 模式不支持文件夹选择，显示提示
   */
  const selectFolder = async (): Promise<string | null> => {
    message.warning('Web 模式暂不支持文件夹选择，请使用桌面版本')
    logger.warn('Web 模式：用户尝试选择文件夹但不支持')
    return null
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
          .flatMap(f => f.extensions.map(e => `.${e}`))
          .join(',')
      }

      input.onchange = (e) => {
        const files = (e.target as HTMLInputElement).files
        if (!files || files.length === 0) {
          resolve([])
          return
        }

        const fileNames = Array.from(files).map(f => f.name)
        resolve(fileNames)
        logger.info(`已选择 ${fileNames.length} 个文件`)
      }

      input.click()
    })
  }

  return {
    selectFile,
    selectFolder,
    selectFiles,
  }
}
