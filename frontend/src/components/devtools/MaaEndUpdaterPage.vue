<template>
  <div class="maaend-updater-page">
    <section class="debug-section">
      <h4>🔄 MaaEnd 外部更新器</h4>
      <p class="hint">仅开发环境可用。下载源和安装包获取由 runtime/MAAFW-Updater 负责。</p>

      <label class="field">
        <span>脚本</span>
        <select v-model="selectedScriptId" :disabled="loading || running">
          <option value="" disabled>请选择 MaaEnd 脚本</option>
          <option v-for="script in maaEndScripts" :key="script.uid" :value="script.uid">
            {{ script.name }} ({{ script.uid }})
          </option>
        </select>
      </label>

      <label class="field">
        <span>Updater 路径</span>
        <input v-model="form.updaterPath" placeholder="由 MAAFW_UPDATER_PATH 或 cwd 提供" />
      </label>

      <label class="field">
        <span>当前版本</span>
        <input v-model="form.currentVersion" placeholder="例如 v4.5.2" />
      </label>

      <label class="field">
        <span>平台（可选）</span>
        <input v-model="form.platform" placeholder="例如 linux-x86_64，留空自动识别" />
      </label>

      <label class="field">
        <span>等待 PID（可选）</span>
        <input v-model="form.waitPid" inputmode="numeric" placeholder="例如 12345" />
      </label>

      <label class="field">
        <span>重启入口（可选）</span>
        <input v-model="form.relaunch" placeholder="例如 MaaEnd" />
      </label>

      <div class="actions">
        <button class="action-btn" :disabled="loading || running" @click="loadScripts">
          {{ loading ? '读取中...' : '刷新脚本' }}
        </button>
        <button class="action-btn primary" :disabled="loading || running" @click="runUpdate">
          {{ running ? '更新中...' : '执行更新' }}
        </button>
      </div>
    </section>

    <section v-if="lastMessage" class="debug-section">
      <h4>📋 执行结果</h4>
      <div class="result" :class="{ success: lastSuccess, error: !lastSuccess }">
        {{ lastMessage }}
      </div>
      <pre v-if="lastData">{{ formatJson(lastData) }}</pre>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useScriptApi } from '@/composables/useScriptApi'
import { maaEndUpdaterDebugApi } from '@/services/maaEndUpdaterDebugApi'

const logger = window.electronAPI.getLogger('MaaEnd 更新器调试')
const { getScripts } = useScriptApi()

type MaaEndScript = { uid: string; name: string }

const maaEndScripts = ref<MaaEndScript[]>([])
const selectedScriptId = ref('')
const loading = ref(false)
const running = ref(false)
const lastMessage = ref('')
const lastSuccess = ref(false)
const lastData = ref<Record<string, unknown> | null>(null)
const form = reactive({
  updaterPath: '',
  currentVersion: '',
  platform: '',
  waitPid: '',
  relaunch: '',
})

const loadScripts = async () => {
  loading.value = true
  try {
    const scripts = await getScripts(false)
    maaEndScripts.value = scripts
      .filter(script => script.type === 'MaaEnd')
      .map(script => ({ uid: script.uid, name: script.name }))
    if (!maaEndScripts.value.some(script => script.uid === selectedScriptId.value)) {
      selectedScriptId.value = maaEndScripts.value[0]?.uid || ''
    }
    if (!maaEndScripts.value.length) {
      message.warning('当前没有已配置的 MaaEnd 脚本')
    }
  } catch (error) {
    logger.error('读取 MaaEnd 脚本失败', error)
    message.error(`读取 MaaEnd 脚本失败: ${String(error)}`)
  } finally {
    loading.value = false
  }
}

const runUpdate = async () => {
  if (!selectedScriptId.value) {
    message.warning('请先选择 MaaEnd 脚本')
    return
  }
  if (!form.currentVersion.trim()) {
    message.warning('请填写当前 MaaEnd 版本')
    return
  }

  running.value = true
  lastMessage.value = ''
  lastData.value = null
  try {
    const response = await maaEndUpdaterDebugApi.update({
      scriptId: selectedScriptId.value,
      updaterPath: form.updaterPath.trim() || undefined,
      currentVersion: form.currentVersion.trim(),
      platform: form.platform.trim() || undefined,
      source: 'auto',
      waitPid: form.waitPid.trim() ? Number(form.waitPid) : undefined,
      relaunch: form.relaunch.trim() || undefined,
    })
    lastSuccess.value = response.code === 200
    lastMessage.value = response.message || (lastSuccess.value ? '更新成功' : '更新失败')
    lastData.value = response.data || null
    if (lastSuccess.value) {
      message.success(lastMessage.value)
    } else {
      message.error(lastMessage.value)
    }
  } catch (error) {
    lastSuccess.value = false
    lastMessage.value = `更新请求失败: ${String(error)}`
    logger.error(lastMessage.value)
    message.error(lastMessage.value)
  } finally {
    running.value = false
  }
}

const formatJson = (data: unknown) => JSON.stringify(data, null, 2)

onMounted(loadScripts)
</script>

<style scoped>
.maaend-updater-page {
  color: #fff;
}

.debug-section {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
}

.debug-section:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.debug-section h4 {
  margin: 0 0 8px;
  color: #4caf50;
  font-size: 11px;
}

.hint {
  margin: 0 0 10px;
  color: #aaa;
  line-height: 1.4;
}

.field {
  display: block;
  margin-bottom: 8px;
}

.field span {
  display: block;
  margin-bottom: 3px;
  color: #aaa;
  font-size: 10px;
}

.field input,
.field select {
  width: 100%;
  padding: 5px 6px;
  border: 1px solid #555;
  border-radius: 4px;
  background: #222;
  color: #fff;
  font-size: 11px;
}

.actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid #555;
  border-radius: 4px;
  background: #333;
  color: #fff;
  cursor: pointer;
  font-size: 11px;
}

.action-btn.primary {
  border-color: #4caf50;
  background: #2e7d32;
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.result {
  padding: 6px;
  border-radius: 4px;
  line-height: 1.4;
}

.result.success {
  background: rgba(76, 175, 80, 0.25);
  color: #9cff9c;
}

.result.error {
  background: rgba(244, 67, 54, 0.25);
  color: #ff9b91;
}

pre {
  max-height: 260px;
  margin: 8px 0 0;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: #ddd;
  font-size: 10px;
}
</style>
