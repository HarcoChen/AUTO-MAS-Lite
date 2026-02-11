# Electron 到 WebUI 迁移模式参考

**文档目的**: 提供已验证的迁移模式和 Web 替代方案参考
**适用范围**: 所有需要 Electron → Web 适配的前端组件和工具函数

---

## 1. 环境检测模式

### ✅ 推荐实现

```typescript
// frontend/src/main.ts (已实现)
const hasRealElectronAPI = typeof window !== 'undefined' &&
  window.electronAPI !== undefined &&
  'installPython' in (window as any).electronAPI

const isElectron = hasRealElectronAPI
export { isElectron }
```

**特点**:
- 使用 `'installPython' in window.electronAPI` 进行可靠判断
- 避免简单的 `typeof window.electronAPI !== 'undefined'` 导致的误判
- 全局导出供整个应用使用

### 使用示例

```typescript
import { isElectron } from '@/main'

if (isElectron) {
  // Electron 特定逻辑
  const result = await window.electronAPI.someMethod()
} else {
  // Web 模式逻辑
  const result = await fetch('/api/some-endpoint')
}
```

---

## 2. 条件组件渲染模式

### ✅ Pattern: 隐藏不支持的功能

```vue
<template>
  <div class="component">
    <!-- 仅在 Electron 模式显示 -->
    <div v-if="isElectron" class="electron-only">
      <a-button @click="minimizeWindow">最小化</a-button>
      <a-button @click="maximizeWindow">最大化</a-button>
    </div>

    <!-- 仅在 Web 模式显示提示 -->
    <div v-else class="web-notice">
      <a-alert type="info" message="Web 模式：窗口控制功能不可用" />
    </div>

    <!-- 共享功能 (始终显示) -->
    <div class="shared-content">
      <!-- 跨模式功能 -->
    </div>
  </div>
</template>

<script lang="ts" setup>
import { isElectron } from '@/main'

const minimizeWindow = async () => {
  if (isElectron && window.electronAPI?.windowMinimize) {
    await window.electronAPI.windowMinimize()
  }
}

const maximizeWindow = async () => {
  if (isElectron && window.electronAPI?.windowMaximize) {
    await window.electronAPI.windowMaximize()
  }
}
</script>
```

### ✅ Pattern: 提供 Web 替代方案

```vue
<template>
  <div class="file-selector">
    <a-button @click="selectFile">
      {{ isElectron ? '选择文件' : '上传文件' }}
    </a-button>

    <!-- Web 模式隐藏的文件输入 -->
    <input
      v-if="!isElectron"
      ref="fileInput"
      type="file"
      style="display: none"
      @change="handleFileSelected"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { isElectron } from '@/main'
import { message } from 'ant-design-vue'

const fileInput = ref<HTMLInputElement>()

const selectFile = async () => {
  if (isElectron && window.electronAPI?.selectFile) {
    const path = await window.electronAPI.selectFile()
    if (path) {
      handleFileSelected({ path })
    }
  } else {
    // Web 模式：触发文件输入
    fileInput.value?.click()
  }
}

const handleFileSelected = (event: any) => {
  const file = event.target?.files?.[0] || event.path
  // 处理选中的文件
  console.log('Selected file:', file)
}
</script>
```

---

## 3. API 调用双路由模式

### ✅ Pattern: 同步配置数据

**场景**: 需要从 Electron IPC 或后端 API 加载数据

```typescript
// utilities/config.ts
import { isElectron } from '@/main'
import { SettingService } from '@/api'

// Electron 模式: 使用 IPC 直接读写文件
// Web 模式: 调用 REST API

export async function loadConfig(): Promise<ConfigData> {
  if (isElectron && window.electronAPI?.loadConfig) {
    try {
      return await window.electronAPI.loadConfig()
    } catch (error) {
      console.error('Failed to load config via IPC:', error)
      // Fallback to API (if available)
    }
  }

  // Web 模式或 Electron fallback
  try {
    const response = await SettingService.getScripts()
    if (response.code === 200) {
      return response.data
    }
    throw new Error(response.message || '加载配置失败')
  } catch (error) {
    console.error('Failed to load config via API:', error)
    throw error
  }
}

export async function saveConfig(data: ConfigData): Promise<void> {
  if (isElectron && window.electronAPI?.saveConfig) {
    try {
      return await window.electronAPI.saveConfig(data)
    } catch (error) {
      console.error('Failed to save config via IPC:', error)
      // Fallback to API
    }
  }

  // Web 模式或 Electron fallback
  try {
    const response = await SettingService.updateScript({ data })
    if (response.code !== 200) {
      throw new Error(response.message || '保存配置失败')
    }
  } catch (error) {
    console.error('Failed to save config via API:', error)
    throw error
  }
}
```

### ✅ Pattern: WebSocket 连接管理

```typescript
// composables/useWebSocket.ts
import { isElectron } from '@/main'
import { logger } from '@/utils/logger'

export function useWebSocket(url: string) {
  const connect = async () => {
    let wsUrl = url

    // Web 模式: 从 API 获取 WebSocket 地址
    if (!isElectron && window.electronAPI?.getApiEndpoint) {
      try {
        const wsEndpoint = await window.electronAPI.getApiEndpoint('websocket')
        wsUrl = wsEndpoint
      } catch (error) {
        logger.error('Failed to get WebSocket endpoint:', error)
        // Fallback to default
        wsUrl = 'ws://localhost:36163/ws'
      }
    }

    // 连接 WebSocket
    const ws = new WebSocket(wsUrl)
    return ws
  }

  const disconnect = () => {
    // 清理逻辑
  }

  return { connect, disconnect }
}
```

---

## 4. 初始化和生命周期模式

### ✅ Pattern: 生命周期自适应

```vue
<template>
  <div class="backend-starter">
    <a-spin v-if="loading" />
    <div v-else>
      <p>{{ statusMessage }}</p>
      <a-button v-if="isElectron && !started" @click="startBackend">
        启动后端
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { isElectron } from '@/main'
import { logger } from '@/utils/logger'

const loading = ref(true)
const statusMessage = ref('')
const started = ref(false)

onMounted(async () => {
  if (!isElectron) {
    // Web 模式: 跳过后端启动步骤
    logger.info('Web 模式：后端需手动启动')
    statusMessage.value = 'Web 模式：后端需手动启动'
    loading.value = false
    return
  }

  // Electron 模式: 启动后端
  try {
    await startBackend()
    statusMessage.value = '后端已启动'
    started.value = true
  } catch (error) {
    statusMessage.value = `启动失败: ${error}`
  }
  loading.value = false
})

const startBackend = async () => {
  if (isElectron && window.electronAPI?.startBackend) {
    return await window.electronAPI.startBackend()
  }
}
</script>
```

---

## 5. 文件操作模式

### ✅ Pattern: 跨模式文件选择

```typescript
// composables/useFileSelection.ts
import { isElectron } from '@/main'
import { message } from 'ant-design-vue'
import { logger } from '@/utils/logger'

interface FileSelectOptions {
  filters?: Array<{ name: string; extensions: string[] }>
  multiple?: boolean
}

export function useFileSelection() {
  const selectFile = async (options: FileSelectOptions = {}): Promise<string | null> => {
    if (isElectron && window.electronAPI?.selectFile) {
      try {
        return await window.electronAPI.selectFile(options)
      } catch (error) {
        logger.error('Failed to select file via dialog:', error)
        message.error('文件选择失败')
        return null
      }
    }

    // Web 模式: 使用 <input type="file">
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

      input.onchange = async (e) => {
        const files = (e.target as HTMLInputElement).files
        if (!files || files.length === 0) {
          resolve(null)
          return
        }

        const file = files[0]
        try {
          // 上传文件到后端，获取路径
          const path = await uploadFileToBackend(file)
          resolve(path)
        } catch (error) {
          logger.error('Failed to upload file:', error)
          message.error('文件上传失败')
          resolve(null)
        }
      }

      input.click()
    })
  }

  const selectFolder = async (): Promise<string | null> => {
    if (isElectron && window.electronAPI?.selectFolder) {
      try {
        return await window.electronAPI.selectFolder()
      } catch (error) {
        logger.error('Failed to select folder:', error)
        return null
      }
    }

    // Web 模式: 提示不支持
    message.warning('Web 模式：文件夹选择功能需要在桌面版中使用')
    return null
  }

  const uploadFileToBackend = async (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/file/upload', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`)
    }

    const result = await response.json()
    if (result.code !== 200) {
      throw new Error(result.message || 'Upload failed')
    }

    return result.message // 返回文件路径
  }

  return { selectFile, selectFolder }
}
```

**使用示例**:

```vue
<template>
  <a-button @click="handleSelectScript">选择脚本</a-button>
</template>

<script lang="ts" setup>
import { useFileSelection } from '@/composables/useFileSelection'

const { selectFile } = useFileSelection()

const handleSelectScript = async () => {
  const path = await selectFile({
    filters: [{ name: 'Scripts', extensions: ['py', 'json'] }]
  })

  if (path) {
    console.log('Selected script:', path)
  }
}
</script>
```

---

## 6. 日志和调试模式

### ✅ Pattern: 统一日志接口

```typescript
// utils/logger.ts (已实现)
// 提供统一的日志接口，自动适配 Electron 和 Web 环境

import { isElectron } from '@/main'

interface Logger {
  info(message: string): void
  warn(message: string): void
  error(message: string, error?: any): void
  debug(message: string): void
}

export const logger: Logger = {
  info: (msg: string) => {
    console.log(`[INFO] ${msg}`)
    if (isElectron && window.electronAPI?.getLogger) {
      window.electronAPI.getLogger('AUTO-MAS').info(msg)
    }
  },
  warn: (msg: string) => {
    console.warn(`[WARN] ${msg}`)
  },
  error: (msg: string, error?: any) => {
    console.error(`[ERROR] ${msg}`, error)
  },
  debug: (msg: string) => {
    console.debug(`[DEBUG] ${msg}`)
  }
}

// 全局使用
export function useLogger(prefix: string): Logger {
  return {
    info: (msg: string) => logger.info(`[${prefix}] ${msg}`),
    warn: (msg: string) => logger.warn(`[${prefix}] ${msg}`),
    error: (msg: string, error?: any) => logger.error(`[${prefix}] ${msg}`, error),
    debug: (msg: string) => logger.debug(`[${prefix}] ${msg}`)
  }
}
```

---

## 7. 通知和用户反馈模式

### ✅ Pattern: 功能限制提示

```typescript
// services/notificationService.ts
import { isElectron } from '@/main'
import { message, notification } from 'ant-design-vue'

export const notificationService = {
  // Electron 窗口聚焦
  focusWindow: async () => {
    if (isElectron && window.electronAPI?.windowFocus) {
      await window.electronAPI.windowFocus()
    } else {
      // Web 模式: 使用浏览器通知 API
      if ('Notification' in window) {
        new Notification('AUTO-MAS', {
          body: '应用需要关注',
          icon: '/icon.png'
        })
      }
    }
  },

  // 显示功能限制通知
  showFeatureNotAvailable: (featureName: string) => {
    message.warning(`Web 模式：${featureName} 功能仅在桌面版中可用`)
  },

  // 显示操作步骤
  showWebModeInfo: (message: string) => {
    notification.info({
      message: 'Web 模式信息',
      description: message,
      duration: 0
    })
  }
}
```

---

## 8. 常见 Electron API 的 Web 替代方案

| Electron API | Web 替代方案 | 难度 | 备注 |
|--------------|------------|------|------|
| `selectFile()` | `<input type="file">` + 后端上传 | ⭐⭐ | 需要后端支持 |
| `selectFolder()` | `<input webkitdirectory>` 或提示 | ⭐⭐ | 跨浏览器支持有限 |
| `showItemInFolder()` | Blob download 或打开新标签页 | ⭐ | 部分功能可保留 |
| `windowMinimize()` | 隐藏按钮 | ⭐ | Web 不支持窗口控制 |
| `windowMaximize()` | 隐藏按钮 | ⭐ | Web 不支持窗口控制 |
| `windowClose()` | 提示关闭浏览器 | ⭐ | Web 无法关闭标签页 |
| `appQuit()` | 提示或 session 清理 | ⭐ | 逻辑需调整 |
| `readFile()` | 后端 API 或 FileReader API | ⭐⭐ | 取决于文件来源 |
| `saveFile()` | Blob download | ⭐ | 浏览器下载功能 |
| `getAppPath()` | 配置存储在 localStorage | ⭐⭐ | 跨标签页同步 |
| `ipcMain/ipcRenderer` | REST API + WebSocket | ⭐⭐ | 架构调整 |
| `openUrl()` | `window.open()` | ⭐ | 部分网站可能被阻止 |

---

## 9. 最佳实践

### ✅ 必做

1. **始终检测环境**
   ```typescript
   if (isElectron && window.electronAPI?.someMethod) {
     // 使用 Electron 功能
   } else {
     // Web fallback
   }
   ```

2. **提供清晰的反馈**
   ```typescript
   if (!isElectron) {
     message.warning('此功能仅在桌面版中可用')
   }
   ```

3. **测试两种模式**
   - 确保 Electron 模式正常工作
   - 确保 Web 模式不崩溃或给出提示

4. **保持数据一致性**
   - 配置、状态等在两种模式下保持同步
   - 使用相同的数据格式

### ❌ 避免

1. **不要假设 electronAPI 存在**
   ```typescript
   // ❌ 错误
   const result = await window.electronAPI.someMethod()

   // ✅ 正确
   if (isElectron && window.electronAPI?.someMethod) {
     const result = await window.electronAPI.someMethod()
   }
   ```

2. **不要在 Web 模式中调用 Electron API 而不检查**
   ```typescript
   // ❌ 错误（会导致运行时错误）
   window.electronAPI.windowClose() // Web 中不存在

   // ✅ 正确
   if (isElectron) {
     window.electronAPI.windowClose()
   }
   ```

3. **不要隐藏所有 UI，应该提供替代方案**
   ```typescript
   // ❌ 不好（用户看不到任何东西）
   if (!isElectron) return null

   // ✅ 好（提供替代方案或清晰提示）
   if (!isElectron) {
     return <message.warning>Web 模式下此功能不可用</message>
   }
   ```

4. **不要假设特定的文件系统路径**
   ```typescript
   // ❌ 错误（Web 模式中文件来自表单上传）
   const path = `/data/config/${fileName}`

   // ✅ 正确（处理不同的文件来源）
   const path = isElectron ? `/data/config/${fileName}` : `uploaded_${fileName}`
   ```

---

## 10. 调试技巧

### 在浏览器中测试 Electron 检测

```javascript
// 在浏览器开发者工具中执行
console.log('isElectron:', typeof window !== 'undefined' &&
  window.electronAPI !== undefined &&
  'installPython' in (window as any).electronAPI)

// 检查 electronAPI 是否存在
console.log('electronAPI:', window.electronAPI)

// 手动注入 fake electronAPI 进行测试（仅调试用）
window.electronAPI = {
  getApiEndpoint: async () => 'http://localhost:36163',
  getLogger: () => console
  // ... 其他方法
}
```

### 在 Electron 中检查 Web API

```javascript
// 在 Electron 主进程中
console.log('Window location:', window.location.href)
console.log('Is using HTTPS:', window.location.protocol === 'https:')

// 检查 Notification API
console.log('Notification available:', 'Notification' in window)
```

---

## 11. 相关文件引用

- **环境检测**: [frontend/src/main.ts](../frontend/src/main.ts)
- **日志系统**: [frontend/src/utils/logger.ts](../frontend/src/utils/logger.ts)
- **配置管理**: [frontend/src/utils/config.ts](../frontend/src/utils/config.ts)
- **WebSocket**: [frontend/src/composables/useWebSocket.ts](../frontend/src/composables/useWebSocket.ts)
- **初始化步骤**: [frontend/src/views/Initialization/index.vue](../frontend/src/views/Initialization/index.vue)
- **API 定义**: [frontend/src/types/electron.d.ts](../frontend/src/types/electron.d.ts)

---

**Last Updated**: 2026-02-11
**Status**: 已验证模式 ✅
