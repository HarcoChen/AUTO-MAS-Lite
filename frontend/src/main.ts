import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.ts'
import { OpenAPI } from '@/api'

import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

// Web 兼容的日志系统 - 检测是否有真实的 Electron API
const hasRealElectronAPI = typeof window !== 'undefined' && window.electronAPI !== undefined && 'installPython' in (window as any).electronAPI
export const isElectron = hasRealElectronAPI

const createLogger = (prefix: string) => ({
  info: (msg: string) => isElectron && window.electronAPI?.logInfo ? window.electronAPI.logInfo(prefix, msg) : console.log(`[${prefix}] ${msg}`),
  error: (msg: string) => isElectron && window.electronAPI?.logError ? window.electronAPI.logError(prefix, msg) : console.error(`[${prefix}] ${msg}`),
  warn: (msg: string) => isElectron && window.electronAPI?.logWarn ? window.electronAPI.logWarn(prefix, msg) : console.warn(`[${prefix}] ${msg}`),
  debug: (msg: string) => isElectron && window.electronAPI?.logDebug ? window.electronAPI.logDebug(prefix, msg) : console.debug(`[${prefix}] ${msg}`),
})
const logger = createLogger('前端主入口')

// 暴露全局 logger 供其他模块使用
window.__GLOBAL_LOGGER__ = {
  createLogger,
  isElectron,
}

// Polyfill: 如果 electronAPI.getLogger 不存在，创建一个兼容的 logger
// 只在确实有 electronAPI 时才添加 polyfill，不创建假的 electronAPI
if (typeof window !== 'undefined' && window.electronAPI) {
  if (!window.electronAPI.getLogger) {
    ;(window as any).electronAPI.getLogger = (prefix: string) => ({
      info: (msg: string) => console.log(`[${prefix}] ${msg}`),
      error: (msg: string) => console.error(`[${prefix}] ${msg}`),
      warn: (msg: string) => console.warn(`[${prefix}] ${msg}`),
      debug: (msg: string) => console.debug(`[${prefix}] ${msg}`),
    })
  }
}

// 导入WebSocket消息监听组件
import WebSocketMessageListener from '@/components/WebSocketMessageListener.vue'

// 正常路由：执行完整初始化
// 配置dayjs中文本地化
dayjs.locale('zh-cn')

// 从 Electron 获取 API 端点并设置 OpenAPI.BASE
if (window.electronAPI?.getApiEndpoint) {
  window.electronAPI.getApiEndpoint('local')
    .then(endpoint => {
      OpenAPI.BASE = endpoint
      logger.info('前端应用开始初始化')
      logger.info(`API基础URL: ${OpenAPI.BASE}`)
    })
    .catch(error => {
      const errorMsg = error instanceof Error ? error.message : String(error)
      logger.error(`获取 API 端点失败，使用默认值: ${errorMsg}`)
      OpenAPI.BASE = 'http://localhost:36163'
      logger.info(`API基础URL (默认): ${OpenAPI.BASE}`)
    })
} else {
  // 非 Electron 环境，使用默认值
  OpenAPI.BASE = 'http://localhost:36163'
  logger.info('前端应用开始初始化')
  logger.info(`API基础URL (默认): ${OpenAPI.BASE}`)
}

// 创建应用实例
const app = createApp(App)

// 注册插件
app.use(Antd)
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  const errorMsg = err instanceof Error ? err.message : String(err)
  logger.error(`Vue应用错误: ${errorMsg}, 组件信息: ${info}`)
}

// 挂载应用
app.mount('#app')

// 注册WebSocket消息监听组件
app.component('WebSocketMessageListener', WebSocketMessageListener)

logger.info('前端应用初始化完成')
