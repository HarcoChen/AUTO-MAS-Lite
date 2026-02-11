# Electron 到 WebUI 迁移进度追踪

**更新时间**: 2026-02-11
**迁移策略**: 优雅降级 (Graceful Degradation)
**目标**: 在保持 Electron 应用完整功能的同时，支持 Web 浏览器运行

---

## 📊 迁移状态总览

| 类别 | 数量 | 状态 | 优先级 |
|------|------|------|--------|
| 已完成 | 8 | ✅ | - |
| 高优先级待处理 | 3 | ⏳ | 🔴 |
| 中优先级待处理 | 13 | ⏳ | 🟠 |
| 低优先级待处理 | 10 | ⏳ | 🟡 |
| **总计** | **34** | - | - |

---

## ✅ 已完成的迁移项

### 1. 环境检测机制
- **文件**: `frontend/src/main.ts:11-13`
- **实现**: 使用 `'installPython' in window.electronAPI` 作为可靠检测标准
- **特性**: 全局 `isElectron` 变量
- **备注**: 确保了精确的运行时环境识别

### 2. 日志系统抽象
- **文件**: `frontend/src/utils/logger.ts`
- **实现**: 统一的日志接口，自动切换 Electron IPC 或 console 输出
- **特性**: 全局日志工厂 `window.__GLOBAL_LOGGER__`
- **备注**: 支持跨模式的统一日志体验

### 3. 初始化流程适配
- **文件**:
  - `frontend/src/views/Initialization/index.vue:277-284`
  - `frontend/src/views/Initialization/components/BackendStartStep.vue:217-229`
- **实现**: Web 模式自动跳过系统环境安装步骤
- **特性**: 显示 "已跳过 (Web 模式)" 状态信息
- **备注**: 用户流程保持连贯

### 4. 静态文件服务
- **文件**: `main.py:179-194`
- **实现**: FastAPI 提供 SPA 支持
- **特性**: Web 模式可访问 `http://localhost:36163` 获取前端静态文件
- **备注**: 支持完整的 Web 部署

### 5. WebSocket CORS 支持
- **文件**: `app/api/core.py:38-43`
- **实现**: WebSocket 端点接受跨域连接
- **特性**: 支持 Vite dev server (5173) → FastAPI (36163) 的连接
- **备注**: 开发模式和生产部署都能正常工作

### 6. Monaco Editor 懒加载
- **文件**: 前端组件中的编辑器调用
- **优化**: 减少初始包体积 3-5MB
- **特性**: 按需加载编辑器脚本
- **备注**: 改善首屏加载体验

### 7. 外部链接处理
- **文件**: `frontend/src/utils/openExternal.ts`
- **实现**: 已有 `window.open()` fallback
- **特性**: 同时支持 Electron `openUrl()` 和浏览器 `window.open()`
- **备注**: 无需进一步修改

### 8. 移除 Electron 开发依赖
- **文件**: `frontend/package.json`
- **实现**: 删除 Electron 相关的 dev dependencies
- **特性**: Web 模式编译更轻量
- **备注**: 减少包体积和依赖复杂度

---

## 🔴 高优先级待处理 (阻碍基本 Web 功能)

### Task 1: TitleBar 窗口控制适配
- **文件**: `frontend/src/components/TitleBar.vue`
- **问题**:
  - Lines 137-191: `windowMinimize()`, `windowMaximize()`, `windowClose()`, `windowIsMaximized()`
  - Line 113: `stopBackend()`
  - Line 166: `appQuit()`
- **影响范围**: 应用标题栏的窗口控制按钮 (最小化、最大化、关闭)
- **建议方案**:
  - 添加 `isElectron` 检测
  - Web 模式隐藏窗口控制按钮
  - 保留其他 TitleBar 功能（标题、设置菜单）
  - `appQuit()` 显示 "Web 模式：请关闭浏览器标签页" 提示
- **实现难度**: ⭐ (简单)
- **预期受益**: 解决 Web 模式下的 UI 异常和运行时错误
- **状态**: ⏳ 待处理

### Task 2: 配置管理 (config.ts) 适配
- **文件**: `frontend/src/utils/config.ts`
- **问题**: Lines 26-130，所有配置读写操作依赖 Electron IPC
  - `loadConfig()` - IPC 调用
  - `saveConfig()` - IPC 调用
  - `resetConfig()` - IPC 调用
- **影响范围**: 整个应用的配置持久化和初始化
- **后端 API 现状**: ✅ 已存在
  - `POST /api/setting/get` - 获取配置 (app/api/setting.py:47-66)
  - `POST /api/setting/update` - 更新配置 (app/api/setting.py:69-92)
- **建议方案**:
  - 创建双模式配置管理器
  - Electron 模式: 使用现有 IPC 方法 (保持不变)
  - Web 模式: 调用后端 API (`SettingService.getScripts()` 和 `SettingService.updateScript()`)
  - 可选: localStorage 缓存减少 API 调用
- **实现难度**: ⭐ (简单)
- **预期受益**: 配置数据在 Web 模式下持久化，支持配置备份和恢复
- **状态**: ⏳ 待处理
- **依赖**: 需确认 OpenAPI 生成的 `SettingService` 已正确导入

### Task 3: 文件选择对话框适配 (6 个文件)
- **影响文件**:
  1. `frontend/src/views/EditView/Script/GeneralScriptEdit.vue`
     - Lines 1419, 1493, 1517, 1548, 1582, 1586, 1625
     - 使用: `selectFile()`, `selectFolder()`, `getAppPath()`
  2. `frontend/src/views/EditView/Script/MAAScriptEdit.vue`
     - Line 494: `selectFolder()`
  3. `frontend/src/views/EditView/User/MAAUserEdit.vue`
     - Line 712: `selectFile()`
  4. `frontend/src/views/EditView/User/GeneralUserEdit.vue`
     - Lines 712, 732: `selectFile()`
  5. `frontend/src/views/Emulator.vue`
     - Line 615: `selectFile()`
- **问题**: Web 浏览器无法直接访问本地文件系统，无法使用 Electron 的文件对话框
- **建议方案**:
  - 创建 `frontend/src/composables/useFileSelection.ts` 通用文件选择函数
  - Electron 模式: 保持现有 `window.electronAPI.selectFile/selectFolder()` 调用
  - Web 模式:
    - 文件选择: 使用 `<input type="file">` 元素，上传到后端
    - 文件夹选择: 显示提示 "Web 模式不支持文件夹选择"
  - 后端需支持: `POST /api/file/upload` 文件上传端点
- **实现难度**: ⭐⭐ (中等)
- **预期受益**: Web 模式下可选择和上传脚本、用户文件等
- **状态**: ⏳ 待处理
- **依赖**: 需实现后端文件上传 API

---

## 🟠 中优先级待处理 (功能受限但不崩溃)

### Task 4: WebSocket 后端管理适配
- **文件**: `frontend/src/composables/useWebSocket.ts`
- **问题**:
  - Line 16: `getApiEndpoint('websocket')`
  - Lines 184, 186: `stopBackend()`
  - Lines 191-192: `startBackend()`
  - Line 465: `appRestart()` (未定义)
  - Lines 466-467, 595-596: `windowClose()`
- **影响范围**: WebSocket 连接管理、后端生命周期控制
- **建议方案**:
  - Web 模式检测后显示提示: "Web 模式：后端需手动启动和管理"
  - Web 模式禁用或隐藏 "停止后端"、"重启应用" 按钮
  - 保持 WebSocket 连接正常工作
- **实现难度**: ⭐ (简单)
- **预期受益**: Web 模式下不会触发错误的后端控制
- **状态**: ⏳ 待处理

### Task 5: 日志查看与导出适配
- **文件**:
  - `frontend/src/views/setting/TabAdvanced.vue`
  - `frontend/src/views/Logs.vue`
  - `frontend/src/components/LogTimestampSelector.vue`
- **问题**:
  - `openLogWindow()` - 打开日志窗口
  - `getLogs()` - 读取日志文件
  - `exportLogs()` - 导出日志
  - `showItemInFolder()` - 在文件管理器中打开
  - `readFile()` - 读取文件内容
- **影响范围**: 日志查看和导出功能
- **建议方案**:
  - 日志查看: 通过后端 API 获取日志，在浏览器中显示
  - 日志导出: 使用 Blob + `download` 属性下载，而不是调用 `showItemInFolder()`
  - 文件读取: 通过后端 API 提供日志内容
- **实现难度**: ⭐⭐ (中等)
- **预期受益**: Web 模式下完整的日志查看和导出能力
- **状态**: ⏳ 待处理

### Task 6: 历史记录导出适配
- **文件**: `frontend/src/views/history/useHistoryLogic.ts`
- **问题**:
  - `showItemInFolder()` - 打开导出文件所在目录
- **影响范围**: 历史记录导出后的文件定位
- **建议方案**:
  - Web 模式: 直接下载文件，不尝试打开文件夹
  - Electron 模式: 保持现有功能
- **实现难度**: ⭐ (简单)
- **预期受益**: Web 模式下正常导出历史记录
- **状态**: ⏳ 待处理

### Task 7-10: 其他中优先级组件
- **相关文件**:
  - `frontend/src/components/WebhookManager.vue`
  - `frontend/src/composables/useUpdateChecker.ts`
  - `frontend/src/composables/useAudioPlayer.ts`
  - `frontend/src/views/queue/components/QueueItemManager.vue`
- **问题**: 零散的 Electron API 使用
- **建议方案**: 针对各组件添加 `isElectron` 检测和 fallback
- **实现难度**: ⭐ (简单)
- **状态**: ⏳ 待处理

---

## 🟡 低优先级待处理 (Nice to have)

### Task 11: 窗口聚焦/通知适配
- **文件**:
  - `frontend/src/components/GlobalPowerCountdown.vue:50`
  - `frontend/src/components/WebSocketMessageListener.vue:57`
- **问题**: `windowFocus()` 调用
- **建议方案**: Web 模式使用 Browser Notification API
- **实现难度**: ⭐ (简单)
- **预期受益**: Web 模式下的通知提示
- **状态**: ⏳ 待处理

### Task 12-14: 开发者工具适配
- **文件**:
  - `frontend/src/components/devtools/BackendLaunchPage.vue`
  - `frontend/src/components/devtools/MessageTestPage.vue`
  - `frontend/src/components/devtools/QuickNavPage.vue`
- **问题**: 后端启动/停止、消息测试等 Electron 专属功能
- **建议方案**: Web 模式显示 "仅在 Electron 模式下可用" 提示
- **实现难度**: ⭐ (简单)
- **预期受益**: 明确指示某些功能的限制
- **状态**: ⏳ 待处理

### Task 15: 其他零散使用
- **文件**:
  - `frontend/src/utils/scheduler-debug.ts`
  - `frontend/src/views/scheduler/schedulerHandlers.ts`
  - `frontend/src/router/index.ts` (已适配)
- **问题**: 零散的 Electron API 使用
- **建议方案**: 添加 `isElectron` 检测
- **实现难度**: ⭐ (简单)
- **状态**: ⏳ 待处理

---

## 🔧 推荐实施顺序

### 第一轮 (高优先级) - 必须完成
1. ✅ TitleBar 窗口控制 - 解决 UI 异常
2. ✅ Config 管理 - 支持配置持久化
3. ✅ 文件选择对话框 - 支持文件操作 + 后端文件上传 API

### 第二轮 (中优先级) - 建议完成
4. WebSocket 后端管理
5. 日志查看与导出
6. 历史记录导出
7. 其他零散组件

### 第三轮 (低优先级) - 可选
8. 通知/窗口聚焦
9. 开发者工具
10. 其他增强功能

---

## 📝 迁移模式参考

### Pattern 1: 组件级环境检测
```typescript
import { isElectron } from '@/main'

if (isElectron && window.electronAPI?.someMethod) {
  await window.electronAPI.someMethod()
} else {
  message.warning('此功能仅在桌面版本中可用')
  // 或提供 Web 替代方案
}
```

### Pattern 2: 条件渲染和逻辑
```vue
<template>
  <div v-if="isElectron" class="window-controls">
    <!-- 仅 Electron 模式显示 -->
  </div>
  <div v-else class="web-info">
    <!-- 仅 Web 模式显示 -->
  </div>
</template>

<script>
import { isElectron } from '@/main'
</script>
```

### Pattern 3: API 调用双路由
```typescript
import { isElectron } from '@/main'
import { SomeService } from '@/api'

export async function loadData() {
  if (isElectron && window.electronAPI?.loadData) {
    return await window.electronAPI.loadData()  // Electron IPC
  } else {
    const response = await SomeService.getData()  // API 调用
    return response.data
  }
}
```

### Pattern 4: 提示和防护
```typescript
if (!isElectron) {
  logger.info('Web 模式：该功能不可用')
  return null
}
// Electron 专属逻辑
```

---

## 📋 测试清单

### Electron 模式验证
- [ ] 所有 Electron API 调用正常
- [ ] 窗口控制（最小化、最大化、关闭）正常
- [ ] 配置读写正常
- [ ] 文件选择对话框正常
- [ ] 无新增错误或警告
- [ ] 性能无明显变化

### Web 模式验证 (浏览器)
```bash
# 启动后端
python main.py

# 启动前端 dev server
cd frontend && yarn dev

# 访问 http://localhost:5173
```

**功能测试**:
- [ ] 应用可正常加载
- [ ] 无 Electron API 相关错误
- [ ] TitleBar 窗口控制按钮隐藏
- [ ] 配置页面加载和保存成功
- [ ] 文件选择触发文件上传
- [ ] WebSocket 连接正常
- [ ] 主要业务功能可用

**浏览器兼容性**:
- [ ] Chrome (最新版)
- [ ] Firefox (最新版)
- [ ] Edge (最新版)
- [ ] Safari (macOS 上测试)

**性能指标**:
- [ ] 首屏加载 < 5 秒
- [ ] API 响应时间 < 500ms
- [ ] 文件上传速度合理

---

## 🎯 预期成果

完成本迁移后，AUTO-MAS-Lite 将实现：

1. **完整的双模式支持**
   - Electron 模式: 完整的桌面应用功能
   - Web 模式: 在浏览器中运行的简化版本

2. **无缝的用户体验**
   - 配置数据同步
   - 统一的 UI 和操作流程
   - 清晰的功能限制提示

3. **更广泛的使用场景**
   - 容器化部署 (Docker)
   - 云端 Web 访问
   - 跨平台浏览器使用 (不限 Windows)

4. **降低维护成本**
   - 单一代码库
   - 统一的开发流程
   - 自动化测试覆盖

---

## 📞 相关文档

- [CLAUDE.md](../CLAUDE.md) - 项目开发指南
- [web-migration-patterns.md](./web-migration-patterns.md) - 迁移模式详解
- [BUILD_GUIDE.md](./BUILD_GUIDE.md) - 构建指南
- [GETTING_STARTED.md](./GETTING_STARTED.md) - 快速开始

---

**Last Updated**: 2026-02-11
**Author**: Claude Code
**Status**: 迁移进行中 (Phase 2: 高优先级实施)
