<!-- eslint-disable vue/no-mutating-props -->
<template>
  <div class="form-section">
    <div class="section-header">
      <h3>任务配置</h3>
    </div>

    <a-alert v-if="modeNotice" :message="modeNotice" type="info" show-icon class="mode-notice" />

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    formData: any
    loading?: boolean
    mode?: string
    source?: 'script' | 'user'
    controllerType?: string | null
  }>(),
  {
    loading: false,
    mode: '详细',
    source: 'user',
    controllerType: null,
  }
)

defineEmits<{
  save: [key: string, value: any]
  saveBatch: [changes: { key: string; value: any }[]]
}>()

const showManagedTaskConfig = computed(
  () => !(props.source === 'user' && props.mode === '简洁') && props.mode !== '自定义'
)

const modeNotice = computed(() => {
  if (showManagedTaskConfig.value) {
    return ''
  }
  if (props.source === 'script') {
    return ''
  }
  if (props.mode === '简洁') {
    return '简洁模式使用脚本级预设配置，请在脚本配置页调整任务开关和选项。'
  }
  if (props.mode === '自定义') {
    return '自定义模式运行用户完整 MaaEnd 配置，MAS 不托管业务任务队列。'
  }
  return ''
})
</script>

<style scoped>
.form-section {
  margin-bottom: 32px;
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--ant-color-border-secondary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mode-notice {
  margin-bottom: 16px;
}

.task-switch-layout {
  display: grid;
  grid-template-columns: minmax(240px, 300px) minmax(360px, 1fr);
  gap: 24px;
  margin-bottom: 20px;
}

.task-group-sidebar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-group-item {
  width: 100%;
  min-height: 52px;
  padding: 10px 12px;
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 8px;
  background: var(--ant-color-bg-container);
  color: var(--ant-color-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  text-align: left;
  transition:
    border-color 0.2s ease,
    background 0.2s ease;
}

.task-group-item.active {
  border-color: var(--ant-color-primary);
  background: var(--ant-color-primary-bg);
}

.task-group-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-group-title {
  font-size: 14px;
  font-weight: 600;
}

.task-group-count {
  color: var(--ant-color-text-secondary);
  font-size: 12px;
}

.task-group-detail {
  min-height: 220px;
  padding: 4px 0;
}

.task-group-detail-header {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--ant-color-text);
  font-size: 15px;
  font-weight: 600;
}

.task-switch-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px 20px;
}

.task-switch-row {
  min-height: 44px;
  padding: 8px 0;
  border-bottom: 1px solid var(--ant-color-border-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.task-switch-label {
  color: var(--ant-color-text);
  font-size: 14px;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--ant-color-text);
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header h3::before {
  content: '';
  width: 4px;
  height: 24px;
  background: linear-gradient(135deg, var(--ant-color-primary), var(--ant-color-primary-hover));
  border-radius: 2px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--ant-color-text);
  font-size: 14px;
}

.help-icon {
  color: var(--ant-color-text-tertiary);
  font-size: 14px;
  cursor: help;
  transition: color 0.3s ease;
}

.help-icon:hover {
  color: var(--ant-color-primary);
}

@media (max-width: 900px) {
  .task-switch-layout {
    grid-template-columns: 1fr;
  }

  .task-group-sidebar {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .task-switch-list {
    grid-template-columns: 1fr;
  }
}
</style>
