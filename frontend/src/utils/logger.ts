// Web 兼容的日志系统 - 共享模块
export function createLogger(prefix: string) {
  return {
    info: (msg: string) => console.log(`[${prefix}] ${msg}`),
    error: (msg: string) => console.error(`[${prefix}] ${msg}`),
    warn: (msg: string) => console.warn(`[${prefix}] ${msg}`),
    debug: (msg: string) => console.debug(`[${prefix}] ${msg}`),
  }
}

// 便捷函数：快速创建 logger
export const log = {
  info: (msg: string) => console.log(msg),
  error: (msg: string) => console.error(msg),
  warn: (msg: string) => console.warn(msg),
  debug: (msg: string) => console.debug(msg),
}
