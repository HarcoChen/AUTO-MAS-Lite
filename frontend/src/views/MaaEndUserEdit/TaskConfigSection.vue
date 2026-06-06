<!-- eslint-disable vue/no-mutating-props -->
<template>
  <div class="form-section">
    <div class="section-header">
      <h3>任务配置</h3>
    </div>

    <a-alert v-if="modeNotice" :message="modeNotice" type="info" show-icon class="mode-notice" />

    <div v-if="showManagedTaskConfig" class="task-config-shell">


      <aside class="task-subnav">
        <div class="task-subnav-header">
          <div>
            <div class="task-subnav-title">可选任务</div>
            <div class="task-subnav-subtitle">点击选择并切换启用状态</div>
          </div>
        </div>

        <a-spin :spinning="loadingState">
          <div class="task-list">
            <template v-for="group in groups" :key="group.name">
              <a-divider v-if="getTasksByGroup(group.name).length > 0" orientation="left" style="margin: 12px 0 8px; font-size: 13px;">{{ group.label || group.name }}</a-divider>
              <button
                v-for="task in getTasksByGroup(group.name)"
                :key="task.name"
                type="button"
                class="task-button"
                :class="{ active: activeTask === task.name }"
                @click="() => { selectTask(task.name); toggleTask(task.name); }"
              >
                <span class="task-button-main">
                  <span class="task-button-title">{{ task.label || task.name }}</span>
                </span>
                <span
                  class="task-state"
                  :class="{ enabled: isTaskEnabled(task.name) }"
                >
                  {{ isTaskEnabled(task.name) ? '已启用' : '未启用' }}
                </span>
              </button>
            </template>
            <div v-if="groups.length === 0" class="empty-hint">
              没有可用的任务
            </div>
          </div>
        </a-spin>
      </aside>

      <section class="task-detail">
        <a-spin :spinning="loadingState">
          <template v-if="activeTaskDefinition">
            <div class="task-detail-header">
              <div class="task-detail-main">
                <div class="task-detail-title-row">
                  <h4 class="task-detail-title">
                    {{ activeTaskDefinition.label || activeTaskDefinition.name }}
                  </h4>
                </div>
              </div>

              <div class="task-detail-actions">
                <span
                  class="task-status-badge"
                  :class="{ enabled: isTaskEnabled(activeTaskDefinition.name) }"
                >
                  {{ isTaskEnabled(activeTaskDefinition.name) ? '已加入预设' : '未加入预设' }}
                </span>
                <a-button
                  :type="isTaskEnabled(activeTaskDefinition.name) ? 'default' : 'primary'"
                  size="large"
                  @click="toggleTask(activeTaskDefinition.name)"
                >
                  {{ isTaskEnabled(activeTaskDefinition.name) ? '停用任务' : '启用任务' }}
                </a-button>
              </div>
            </div>

            <div v-if="isTaskEnabled(activeTaskDefinition.name)" class="task-detail-body">
              <div
                v-if="activeTaskDefinition.option && activeTaskDefinition.option.length > 0"
                class="task-options-panel"
              >
                <MaaEndTaskOptionRenderer
                  :options="activeTaskDefinition.option"
                  :option-definitions="optionDefinitions"
                  :model-value="getTaskOptionValues(activeTaskDefinition.name)"
                  @update:modelValue="handleTaskOptionsUpdate(activeTaskDefinition.name, $event)"
                />
              </div>

              <div v-else class="empty-state">
                这个任务当前没有额外可配置项。
              </div>
            </div>

            <div v-else class="empty-state">
              点击右上角按钮后，这个任务会加入预设队列，再显示详细配置项。
            </div>
          </template>

          <div v-else class="empty-state">
            选择左侧任务以查看详细配置。
          </div>
        </a-spin>
      </section>

      <aside class="task-queue">
        <div class="task-queue-header">
          <div>
            <div class="task-queue-title">任务队列</div>
            <div class="task-queue-subtitle">运行顺序会按这里的排列执行</div>
          </div>
        </div>

        <a-spin :spinning="loadingState">
          <draggable
            v-if="queuedTasks.length > 0"
            v-model="draggableTasks"
            item-key="name"
            :animation="200"
            handle=".drag-handle"
            ghost-class="queue-ghost"
            class="queue-list"
          >
            <template #item="{ element: task, index }">
              <div
                class="queue-item"
                :class="{ active: activeTask === task.name }"
                @click="selectTask(task.name)"
              >
                <div class="queue-item-main">
                  <HolderOutlined class="drag-handle" />
                  <span class="queue-index">{{ Number(index) + 1 }}</span>
                  <span class="queue-name">{{ task.label || task.name }}</span>
                </div>
                <div class="queue-actions">
                  <a-button
                    type="text"
                    size="small"
                    :disabled="Number(index) === 0"
                    @click.stop="moveTaskUp(Number(index))"
                  >
                    <UpOutlined />
                  </a-button>
                  <a-button
                    type="text"
                    size="small"
                    :disabled="Number(index) === draggableTasks.length - 1"
                    @click.stop="moveTaskDown(Number(index))"
                  >
                    <DownOutlined />
                  </a-button>
                  <a-button
                    type="text"
                    size="small"
                    danger
                    @click.stop="removeTask(task.name)"
                  >
                    <DeleteOutlined />
                  </a-button>
                </div>
              </div>
            </template>
          </draggable>

          <div v-else class="empty-state">
            还没有加入任何任务。先从中间区域选中任务，再点击“启用任务”。
          </div>
        </a-spin>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Service } from '@/api'
import { DeleteOutlined, DownOutlined, UpOutlined, HolderOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import MaaEndTaskOptionRenderer from './MaaEndTaskOptionRenderer.vue'

const props = withDefaults(
  defineProps<{
    formData: any
    loading?: boolean
    mode?: string
    source?: 'script' | 'user'
    controllerType?: string | null
    scriptId?: string
    schemaData?: Record<string, any> | null
    schemaLoading?: boolean
  }>(),
  {
    loading: false,
    mode: '详细',
    source: 'user',
    controllerType: null,
    scriptId: undefined,
    schemaData: null,
    schemaLoading: false,
  }
)

const emit = defineEmits<{
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

type TaskDefinition = {
  name: string
  label?: string
  group?: string[]
  _option_definitions?: Record<string, any>
  option?: any[]
  [key: string]: any
}

type GroupDefinition = {
  name: string
  label?: string
  [key: string]: any
}

const groups = ref<GroupDefinition[]>([])
const availableTasks = ref<TaskDefinition[]>([])
const optionDefinitions = ref<Record<string, any>>({})
const activeGroup = ref('')
const activeTask = ref('')
const isFetching = ref(false)
const HIDDEN_TASK_NAMES = new Set<string>(["GearAssembly","PuzzleSolver","BatchUseDetector","ImportBluePrints","ReadAllWiki","BakerEntry","AccountSwitch","WebEvent202605","ReceiveProdManual","StashBackpack"])
const HIDDEN_GROUP_NAMES = new Set<string>(["realtime"])

const loadingState = computed(() => props.loading || props.schemaLoading || isFetching.value)

const getTasksByGroup = (groupName: string) =>
  availableTasks.value.filter(task => task.group && task.group.includes(groupName))

const activeTaskDefinition = computed(() =>
  availableTasks.value.find(task => task.name === activeTask.value) || null
)

const queuedTasks = computed(() =>
  props.formData.Task.EnabledTasks.map((taskName: string) => {
    const taskDefinition = availableTasks.value.find(task => task.name === taskName)
    return taskDefinition || { name: taskName, label: taskName }
  })
)

const draggableTasks = computed({
  get: () => queuedTasks.value,
  set: (val) => {
    const enabledTasks = val.map((task: any) => task.name)
    props.formData.Task.EnabledTasks = enabledTasks
    emit('save', 'Task.EnabledTasks', enabledTasks)
  }
})

const ensureActiveSelection = () => {
  if (!availableTasks.value.length) {
    activeTask.value = ''
    return
  }
  const taskNames = availableTasks.value.map(task => task.name)
  if (!taskNames.includes(activeTask.value)) {
    const enabledTask = availableTasks.value.find(task => isTaskEnabled(task.name))
    activeTask.value = enabledTask?.name || taskNames[0]
  }
}

const applySchemaData = (data: Record<string, any>) => {
  const filteredTasks = (data.tasks || []).filter(
    (task: any) =>
      !HIDDEN_TASK_NAMES.has(String(task.name || '')) &&
      !(Array.isArray(task.group) && task.group.some((group: string) => HIDDEN_GROUP_NAMES.has(group)))
  )
  const visibleGroupNames = new Set(
    filteredTasks.flatMap((task: any) => (Array.isArray(task.group) ? task.group : []))
  )

  groups.value = (data.groups || []).filter(
    (group: any) => !HIDDEN_GROUP_NAMES.has(group.name) && visibleGroupNames.has(group.name)
  )
  availableTasks.value = filteredTasks

  const definitions: Record<string, any> = {}
  for (const task of availableTasks.value) {
    if (task._option_definitions) {
      Object.assign(definitions, task._option_definitions)
    }
  }
  optionDefinitions.value = definitions
  ensureActiveSelection()
}

const loadTasks = async () => {
  if (!props.scriptId || !showManagedTaskConfig.value) return
  if (props.schemaData) {
    applySchemaData(props.schemaData)
    return
  }

  isFetching.value = true
  try {
    const response = await Service.getMaaendAvailableTasksApiScriptsMaaendTasksAvailablePost({
      scriptId: props.scriptId,
    })
    if (response.data) {
      applySchemaData(response.data)
    }
  } catch (error) {
    console.error('Failed to load MaaEnd tasks', error)
  } finally {
    isFetching.value = false
  }
}

const isTaskEnabled = (taskName: string) => props.formData.Task.EnabledTasks.includes(taskName)

const getTaskCount = (groupName: string) =>
  availableTasks.value.filter(task => task.group && task.group.includes(groupName)).length

const getEnabledTaskCount = (groupName: string) =>
  availableTasks.value
    .filter(task => task.group && task.group.includes(groupName))
    .filter(task => isTaskEnabled(task.name)).length

const getTaskOptionValues = (taskName: string) => props.formData.Task.OptionValues[taskName] || {}

const selectTask = (taskName: string) => {
  activeTask.value = taskName
}

const updateEnabledTasks = (taskName: string, enabled: boolean) => {
  const currentEnabled = [...props.formData.Task.EnabledTasks]
  const index = currentEnabled.indexOf(taskName)

  if (enabled && index === -1) {
    currentEnabled.push(taskName)
  } else if (!enabled && index !== -1) {
    currentEnabled.splice(index, 1)
  }

  props.formData.Task.EnabledTasks = currentEnabled
  emit('save', 'Task.EnabledTasks', currentEnabled)
}

const toggleTask = (taskName: string) => {
  updateEnabledTasks(taskName, !isTaskEnabled(taskName))
}

const reorderEnabledTasks = (enabledTasks: string[]) => {
  props.formData.Task.EnabledTasks = enabledTasks
  emit('save', 'Task.EnabledTasks', enabledTasks)
}

const moveTaskUp = (index: number) => {
  if (index <= 0) return
  const reordered = [...props.formData.Task.EnabledTasks]
  ;[reordered[index - 1], reordered[index]] = [reordered[index], reordered[index - 1]]
  reorderEnabledTasks(reordered)
}

const moveTaskDown = (index: number) => {
  if (index >= props.formData.Task.EnabledTasks.length - 1) return
  const reordered = [...props.formData.Task.EnabledTasks]
  ;[reordered[index], reordered[index + 1]] = [reordered[index + 1], reordered[index]]
  reorderEnabledTasks(reordered)
}

const removeTask = (taskName: string) => {
  const queueIndex = props.formData.Task.EnabledTasks.indexOf(taskName)
  updateEnabledTasks(taskName, false)
  if (activeTask.value === taskName) {
    const nextTask =
      queuedTasks.value[queueIndex + 1]?.name ||
      queuedTasks.value[queueIndex - 1]?.name ||
      availableTasks.value.find(task => task.name !== taskName)?.name ||
      ''
    activeTask.value = nextTask
  }
}

const handleTaskOptionsUpdate = (taskName: string, values: Record<string, any>) => {
  if (!props.formData.Task.OptionValues) {
    props.formData.Task.OptionValues = {}
  }
  props.formData.Task.OptionValues[taskName] = values
  emit('save', 'Task.OptionValues', props.formData.Task.OptionValues)
}

watch(() => props.scriptId, loadTasks)
watch(() => props.controllerType, loadTasks)

watch(
  () => showManagedTaskConfig.value,
  newValue => {
    if (newValue) {
      loadTasks()
    }
  }
)

watch(
  () => props.schemaData,
  newValue => {
    if (newValue && showManagedTaskConfig.value) {
      applySchemaData(newValue)
    }
  }
)

watch(
  () => props.formData.Task.EnabledTasks,
  () => {
    ensureActiveSelection()
  },
  { deep: true }
)

onMounted(loadTasks)
</script>

<style scoped>
.form-section {
  margin-bottom: 32px;
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--ant-color-border-secondary);
}

.mode-notice {
  margin-bottom: 16px;
}

.task-config-shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 320px;
  gap: 16px;
  height: 65vh;
  min-height: 400px;
}

.task-subnav,
.task-queue,
.task-detail {
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 12px;
  background: var(--ant-color-bg-container);
}

.task-subnav,
.task-queue {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.ant-spin-nested-loading) {
  display: flex;
  flex: 1;
  min-height: 0;
}

:deep(.ant-spin-container) {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}


.task-button:hover {
  border-color: var(--ant-color-primary);
}



.task-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-subnav-header {
  padding: 18px 18px 14px;
  border-bottom: 1px solid var(--ant-color-border-secondary);
  background: linear-gradient(180deg, rgba(19, 194, 194, 0.08), rgba(19, 194, 194, 0));
}

.task-subnav-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--ant-color-text);
}

.task-subnav-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
}

.task-button {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 10px;
  background: var(--ant-color-bg-layout);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.task-button.active {
  background: rgba(24, 144, 255, 0.08);
  border-color: var(--ant-color-primary);
  box-shadow: 0 0 0 1px rgba(24, 144, 255, 0.08);
}

.task-button-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-button-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ant-color-text);
}

.task-state,
.task-status-badge {
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--ant-color-fill-tertiary);
  color: var(--ant-color-text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.task-state.enabled,
.task-status-badge.enabled {
  background: rgba(82, 196, 26, 0.14);
  color: #389e0d;
}

.task-detail {
  padding: 22px 24px;
  overflow-y: auto;
}

.task-queue-header {
  padding: 18px 16px 14px;
  border-bottom: 1px solid var(--ant-color-border-secondary);
  background: linear-gradient(180deg, rgba(250, 173, 20, 0.12), rgba(250, 173, 20, 0));
}

.task-queue-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--ant-color-text);
}

.task-queue-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
}

.queue-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.queue-item {
  padding: 10px 10px 10px 12px;
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 10px;
  background: var(--ant-color-bg-layout);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.queue-item:hover {
  border-color: var(--ant-color-primary);
}

.queue-item.active {
  border-color: var(--ant-color-primary);
  background: rgba(24, 144, 255, 0.08);
  box-shadow: 0 0 0 1px rgba(24, 144, 255, 0.08);
}

.queue-ghost {
  opacity: 0.5;
  background: var(--ant-color-primary-bg);
  border-style: dashed;
}

.drag-handle {
  cursor: grab;
  color: var(--ant-color-text-tertiary);
  margin-right: 4px;
  font-size: 14px;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle:hover {
  color: var(--ant-color-text);
}

.queue-item-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.queue-index {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: var(--ant-color-fill-tertiary);
  color: var(--ant-color-text-secondary);
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.queue-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ant-color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.task-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--ant-color-border-secondary);
}

.task-detail-main {
  min-width: 0;
}

.task-detail-eyebrow {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--ant-color-primary);
  text-transform: uppercase;
}

.task-detail-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.task-detail-title {
  margin: 0;
  font-size: 22px;
  line-height: 1.25;
  color: var(--ant-color-text);
}

.task-detail-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-detail-body {
  margin-top: 20px;
}

.task-options-panel {
  border-radius: 12px;
  background: var(--ant-color-bg-layout);
}

.empty-state,
.empty-hint {
  padding: 24px 16px;
  border: 1px dashed var(--ant-color-border);
  border-radius: 10px;
  color: var(--ant-color-text-secondary);
  font-size: 14px;
  line-height: 1.6;
  background: var(--ant-color-fill-quaternary);
}

@media (max-width: 1280px) {
  .task-config-shell {
    grid-template-columns: 160px 200px minmax(0, 1fr) 220px;
  }
}

@media (max-width: 1100px) {
  .task-config-shell {
    grid-template-columns: 1fr 1fr;
  }

  .task-detail-header {
    flex-direction: column;
  }

  .task-detail-actions {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 768px) {
  .group-list {
    padding: 12px;
  }

  .task-config-shell {
    grid-template-columns: 1fr;
  }

  .task-detail {
    padding: 18px;
  }

  .task-detail-title {
    font-size: 18px;
  }

  .task-detail-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
