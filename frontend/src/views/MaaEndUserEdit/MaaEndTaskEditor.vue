<template>
  <div class="maaend-task-editor">
    <div class="editor-header">
      <div>
        <h3>快速任务配置</h3>
        <div v-if="previewData" class="project-meta">
          {{ previewData.project.label || previewData.project.name }}
          <span v-if="previewData.project.version">v{{ previewData.project.version }}</span>
        </div>
      </div>
      <a-space>
        <a-button
          v-if="mxuImportAvailable"
          :loading="mxuLoading"
          :disabled="!projectPath"
          @click="openMxuImport"
        >
          <template #icon><ImportOutlined /></template>
          从 MXU 导入
        </a-button>
        <a-button
          :loading="interfaceLoading"
          :disabled="!projectPath"
          @click="reloadInterface(true)"
        >
          <template #icon><ReloadOutlined /></template>
          重新读取 Interface
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="!projectPath"
      type="warning"
      show-icon
      message="请先在脚本配置中设置 MaaEnd 项目目录"
    />

    <div v-else-if="interfaceLoading" class="editor-state">
      <a-spin tip="正在解析 interface.json..." />
    </div>

    <a-alert
      v-else-if="loadError"
      type="error"
      show-icon
      message="Interface 读取失败"
      :description="loadError"
    >
      <template #action>
        <a-button size="small" @click="reloadInterface(true)">重试</a-button>
      </template>
    </a-alert>

    <template v-else-if="previewData">
      <a-row :gutter="16" class="context-row">
        <a-col :xs="24" :md="8">
          <a-form-item label="Controller">
            <a-select
              :value="effectiveControllerName"
              :options="controllerSelectOptions"
              :disabled="controllerSelectOptions.length <= 1"
              @change="handleControllerChange"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-form-item label="Resource">
            <a-select
              :value="effectiveResourceName"
              :options="resourceSelectOptions"
              :disabled="resourceSelectOptions.length <= 1"
              @change="handleResourceChange"
            />
          </a-form-item>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-form-item label="任务预设">
            <a-select
              :value="selectedPreset || undefined"
              allow-clear
              placeholder="选择预设"
              :options="presetSelectOptions"
              @change="handlePresetChange"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="16" class="task-layout">
        <a-col :xs="24" :lg="11">
          <div class="panel-header">
            <span>任务队列</span>
            <a-select
              class="add-task-select"
              :value="undefined"
              show-search
              placeholder="添加任务"
              :disabled="availableTasks.length === 0"
              :options="availableTaskOptions"
              :filter-option="filterSelectOption"
              @change="addTask"
            />
          </div>

          <a-empty
            v-if="orderedTasks.length === 0"
            description="选择预设或添加任务"
            class="task-empty"
          />
          <draggable
            v-else
            v-model="queuedTaskNames"
            :item-key="getTaskKey"
            handle=".drag-handle"
            :animation="160"
            ghost-class="task-row-ghost"
            class="task-list"
            @end="clearPreset"
          >
            <template #item="{ element: taskName }">
              <div
                class="task-row"
                :class="{ 'task-row-selected': selectedTask?.name === taskName }"
                @click="selectedTaskName = taskName"
              >
                <DragOutlined class="drag-handle" aria-label="拖动排序" />
                <img
                  v-if="resolveAssetUrl(taskByName.get(taskName)?.icon)"
                  :src="resolveAssetUrl(taskByName.get(taskName)?.icon)"
                  alt=""
                  class="task-icon"
                />
                <span class="task-name">{{ getTaskLabel(taskName) }}</span>
                <a-button
                  type="text"
                  danger
                  size="small"
                  aria-label="移除任务"
                  @click.stop="removeTask(taskName)"
                >
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </div>
            </template>
          </draggable>
        </a-col>

        <a-col :xs="24" :lg="13">
          <div class="option-panel">
            <template v-if="selectedTask">
              <div class="selected-task-header">
                <div>
                  <h4>{{ getDisplayName(selectedTask) }}</h4>
                  <span>{{ selectedTask.entry }}</span>
                </div>
              </div>
              <MaaFWDescriptionView
                v-if="selectedTask.description"
                :content="selectedTask.description"
                :base-path="previewData.path"
                class="task-description"
              />
              <MaaFWTaskOptionEditor
                :option-names="getTaskOptionNames(selectedTask)"
                :options="previewData.options"
                :task-options="taskSnapshot.taskOptions[selectedTask.name] || {}"
                :controller-name="effectiveControllerName"
                :resource-name="effectiveResourceName"
                :base-path="previewData.path"
                @update="payload => handleTaskOptionUpdate(selectedTask.name, payload)"
              />
            </template>
            <a-empty v-else description="从左侧选择任务后配置选项" />
          </div>
        </a-col>
      </a-row>
    </template>

    <a-modal
      v-model:open="mxuModalOpen"
      title="从 MXU 导入任务配置"
      ok-text="导入到当前用户"
      cancel-text="取消"
      :confirm-loading="mxuLoading"
      :ok-button-props="{ disabled: !mxuPreview }"
      @ok="applyMxuImport"
    >
      <a-form v-if="mxuPreview" layout="vertical">
        <a-form-item label="MXU 实例">
          <a-select
            :value="mxuPreview.selected_instance_id"
            :options="mxuInstanceOptions"
            :loading="mxuLoading"
            @change="selectMxuInstance"
          />
        </a-form-item>
        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item label="Controller">
            {{ mxuPreview.controller || '未设置' }}
          </a-descriptions-item>
          <a-descriptions-item label="Resource">
            {{ mxuPreview.resource || '未设置' }}
          </a-descriptions-item>
          <a-descriptions-item label="启用任务">
            {{ selectedMxuInstance?.enabled_task_count || 0 }} /
            {{ selectedMxuInstance?.task_count || 0 }}
          </a-descriptions-item>
        </a-descriptions>
        <a-alert
          v-if="mxuPreview.warnings.length"
          class="import-warning"
          type="warning"
          show-icon
          message="导入时有以下提示"
          :description="mxuPreview.warnings.join('；')"
        />
        <a-alert
          v-else
          class="import-warning"
          type="success"
          show-icon
          message="配置与当前 Interface 匹配"
        />
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import type { SelectProps } from 'ant-design-vue'
import { message } from 'ant-design-vue'
import { DeleteOutlined, DragOutlined, ImportOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import { buildMaaFWAssetUrl, useMaaFWApi } from '@/composables/useMaaFWApi'
import { useMxuImportApi, type MxuImportPreview } from '@/composables/useMxuImportApi'
import MaaFWDescriptionView from '@/views/EditView/User/MaaFWDescriptionView.vue'
import MaaFWTaskOptionEditor from '@/views/EditView/User/MaaFWTaskOptionEditor.vue'
import type {
  MaaFWControllerInfo,
  MaaFWInterfacePreviewData,
  MaaFWTaskInfo,
  MaaFWTaskOptionValue,
  MaaFWTaskSnapshot,
} from '@/types/script'

interface MaaEndTaskEditorModel {
  controller: string
  resource: string
  selectedPreset: string
  taskSnapshot: string | MaaFWTaskSnapshot
}

const props = withDefaults(
  defineProps<{
    projectPath: string
    controllerType?: 'Win32' | 'Adb'
    modelValue: MaaEndTaskEditorModel
  }>(),
  {
    controllerType: 'Win32',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: MaaEndTaskEditorModel]
}>()

const { loading: interfaceLoading, previewInterface } = useMaaFWApi()
const { loading: mxuLoading, checkMxuImportAvailable, previewMxuConfig } = useMxuImportApi()
const previewData = shallowRef<MaaFWInterfacePreviewData | null>(null)
const mxuPreview = shallowRef<MxuImportPreview | null>(null)
const mxuModalOpen = ref(false)
const mxuImportAvailable = ref(false)
const loadError = ref('')
const selectedTaskName = ref('')
const selectedPreset = ref('')
const controllerName = ref('')
const resourceName = ref('')
const taskSnapshot = ref<MaaFWTaskSnapshot>({
  taskOrder: [],
  taskChecked: {},
  taskOptions: {},
})

type DisplayItem = { name: string; label?: string | null }

const getDisplayName = (item: DisplayItem) => item.label || item.name
const taskByName = computed(
  () => new Map((previewData.value?.tasks || []).map(task => [task.name, task] as const))
)
const controllerOptions = computed(() =>
  (previewData.value?.controllers || []).filter(
    controller => controller.type === props.controllerType
  )
)
const effectiveControllerName = computed(() => {
  if (controllerOptions.value.some(item => item.name === controllerName.value)) {
    return controllerName.value
  }
  return controllerOptions.value[0]?.name || ''
})
const resourceOptions = computed(() =>
  (previewData.value?.resources || []).filter(
    resource =>
      resource.controller.length === 0 ||
      resource.controller.includes(effectiveControllerName.value)
  )
)
const effectiveResourceName = computed(() => {
  if (resourceOptions.value.some(item => item.name === resourceName.value)) {
    return resourceName.value
  }
  return resourceOptions.value[0]?.name || ''
})
const effectiveController = computed<MaaFWControllerInfo | undefined>(() =>
  controllerOptions.value.find(item => item.name === effectiveControllerName.value)
)
const effectiveResource = computed(() =>
  resourceOptions.value.find(item => item.name === effectiveResourceName.value)
)
const activeTasks = computed(() =>
  (previewData.value?.tasks || []).filter(task => {
    if (task.controller.length && !task.controller.includes(effectiveControllerName.value)) {
      return false
    }
    if (task.resource.length && !task.resource.includes(effectiveResourceName.value)) {
      return false
    }
    return true
  })
)
const activeTaskNames = computed(() => new Set(activeTasks.value.map(task => task.name)))
const orderedTasks = computed(() =>
  taskSnapshot.value.taskOrder
    .filter(taskName => taskSnapshot.value.taskChecked[taskName] !== false)
    .map(taskName => taskByName.value.get(taskName))
    .filter(
      (task): task is MaaFWTaskInfo => task !== undefined && activeTaskNames.value.has(task.name)
    )
)
const queuedTaskNames = computed({
  get: () => orderedTasks.value.map(task => task.name),
  set: taskNames => {
    taskSnapshot.value.taskOrder = [...taskNames]
    emitModel()
  },
})
const availableTasks = computed(() => {
  const queued = new Set(orderedTasks.value.map(task => task.name))
  return activeTasks.value.filter(task => !queued.has(task.name))
})
const selectedTask = computed(
  () =>
    orderedTasks.value.find(task => task.name === selectedTaskName.value) ||
    orderedTasks.value[0] ||
    null
)
const controllerSelectOptions = computed(() =>
  controllerOptions.value.map(item => ({ label: getDisplayName(item), value: item.name }))
)
const resourceSelectOptions = computed(() =>
  resourceOptions.value.map(item => ({ label: getDisplayName(item), value: item.name }))
)
const presetSelectOptions = computed(() =>
  (previewData.value?.presets || []).map(item => ({
    label: getDisplayName(item),
    value: item.name,
  }))
)
const availableTaskOptions = computed(() =>
  availableTasks.value.map(item => ({ label: getDisplayName(item), value: item.name }))
)
const mxuInstanceOptions = computed(() =>
  (mxuPreview.value?.instances || []).map(instance => ({
    label: `${instance.name}（${instance.enabled_task_count}/${instance.task_count}）`,
    value: instance.id,
  }))
)
const selectedMxuInstance = computed(() =>
  mxuPreview.value?.instances.find(
    instance => instance.id === mxuPreview.value?.selected_instance_id
  )
)

watch(
  () => props.modelValue,
  value => {
    controllerName.value = value.controller || ''
    resourceName.value = value.resource || ''
    selectedPreset.value = value.selectedPreset || ''
    taskSnapshot.value = normalizeSnapshot(value.taskSnapshot, previewData.value)
  },
  { deep: true, immediate: true }
)

watch(
  orderedTasks,
  tasks => {
    if (!tasks.some(task => task.name === selectedTaskName.value)) {
      selectedTaskName.value = tasks[0]?.name || ''
    }
  },
  { immediate: true }
)

watch(
  () => props.projectPath,
  () => {
    void reloadInterface(false)
    void refreshMxuImportAvailability()
  }
)

const parseSnapshot = (
  raw: string | MaaFWTaskSnapshot | null | undefined
): Partial<MaaFWTaskSnapshot> => {
  if (!raw) return {}
  if (typeof raw !== 'string') return raw
  try {
    return JSON.parse(raw) as Partial<MaaFWTaskSnapshot>
  } catch {
    return {}
  }
}

const normalizeSnapshot = (
  raw: string | MaaFWTaskSnapshot | null | undefined,
  preview: MaaFWInterfacePreviewData | null
): MaaFWTaskSnapshot => {
  const parsed = parseSnapshot(raw)
  const taskNames = new Set((preview?.tasks || []).map(task => task.name))
  const order = Array.isArray(parsed.taskOrder)
    ? parsed.taskOrder.filter(taskName => taskNames.size === 0 || taskNames.has(taskName))
    : []
  const checked = Object.fromEntries(
    order.map(taskName => [taskName, parsed.taskChecked?.[taskName] !== false])
  )
  const queued = new Set(order)
  const options = Object.fromEntries(
    Object.entries(parsed.taskOptions || {}).filter(([taskName]) => queued.has(taskName))
  )
  return { taskOrder: order, taskChecked: checked, taskOptions: options }
}

const emitModel = () => {
  emit('update:modelValue', {
    controller: effectiveControllerName.value,
    resource: effectiveResourceName.value,
    selectedPreset: selectedPreset.value,
    taskSnapshot: JSON.stringify(taskSnapshot.value),
  })
}

const refreshMxuImportAvailability = async () => {
  mxuImportAvailable.value = await checkMxuImportAvailable()
}

const loadMxuPreview = async (instanceId?: string) => {
  try {
    mxuPreview.value = await previewMxuConfig(props.projectPath, instanceId)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'MXU 配置解析失败')
  }
}

const openMxuImport = async () => {
  mxuPreview.value = null
  await loadMxuPreview()
  if (mxuPreview.value) mxuModalOpen.value = true
}

const selectMxuInstance = async (instanceId: string) => {
  await loadMxuPreview(instanceId)
}

const applyMxuImport = () => {
  if (!mxuPreview.value) return
  controllerName.value = mxuPreview.value.controller
  resourceName.value = mxuPreview.value.resource
  selectedPreset.value = ''
  taskSnapshot.value = normalizeSnapshot(mxuPreview.value.snapshot, previewData.value)
  selectedTaskName.value = orderedTasks.value[0]?.name || ''
  emitModel()
  mxuModalOpen.value = false
  message.success('已导入 MXU 配置，请保存当前用户配置')
}

const pruneTasksForContext = () => {
  const nextOrder = taskSnapshot.value.taskOrder.filter(taskName =>
    activeTaskNames.value.has(taskName)
  )
  if (nextOrder.length === taskSnapshot.value.taskOrder.length) return
  taskSnapshot.value.taskOrder = nextOrder
  taskSnapshot.value.taskChecked = Object.fromEntries(
    nextOrder.map(taskName => [taskName, taskSnapshot.value.taskChecked[taskName] !== false])
  )
  taskSnapshot.value.taskOptions = Object.fromEntries(
    Object.entries(taskSnapshot.value.taskOptions).filter(([taskName]) =>
      nextOrder.includes(taskName)
    )
  )
}

const reloadInterface = async (showMessage: boolean) => {
  loadError.value = ''
  previewData.value = null
  if (!props.projectPath) return

  const data = await previewInterface(props.projectPath)
  if (!data) {
    loadError.value = '无法解析 MaaEnd 项目中的 interface.json'
    return
  }

  previewData.value = data
  taskSnapshot.value = normalizeSnapshot(props.modelValue.taskSnapshot, data)
  pruneTasksForContext()
  if (showMessage) message.success('Interface 已重新读取')
}

const handleControllerChange = (value: string) => {
  controllerName.value = value
  resourceName.value = ''
  selectedPreset.value = ''
  pruneTasksForContext()
  emitModel()
}

const handleResourceChange = (value: string) => {
  resourceName.value = value
  selectedPreset.value = ''
  pruneTasksForContext()
  emitModel()
}

const handlePresetChange = (value?: string) => {
  selectedPreset.value = value || ''
  if (!value) {
    emitModel()
    return
  }
  const preset = previewData.value?.presets.find(item => item.name === value)
  if (!preset) return
  taskSnapshot.value = normalizeSnapshot(preset.snapshot, previewData.value)
  pruneTasksForContext()
  selectedTaskName.value = taskSnapshot.value.taskOrder[0] || ''
  emitModel()
}

const addTask = (taskName: string) => {
  if (!activeTaskNames.value.has(taskName)) return
  if (!taskSnapshot.value.taskOrder.includes(taskName)) {
    taskSnapshot.value.taskOrder.push(taskName)
  }
  taskSnapshot.value.taskChecked[taskName] = true
  taskSnapshot.value.taskOptions[taskName] ||= {}
  selectedTaskName.value = taskName
  clearPreset()
}

const removeTask = (taskName: string) => {
  taskSnapshot.value.taskChecked[taskName] = false
  clearPreset()
}

const clearPreset = () => {
  selectedPreset.value = ''
  emitModel()
}

const uniqueOptionNames = (groups: string[][]) => {
  const result: string[] = []
  const seen = new Set<string>()
  for (const group of groups) {
    for (const name of group) {
      if (seen.has(name)) continue
      seen.add(name)
      result.push(name)
    }
  }
  return result
}

const getTaskOptionNames = (task: MaaFWTaskInfo) =>
  uniqueOptionNames([
    previewData.value?.globalOption || [],
    effectiveController.value?.option || [],
    effectiveResource.value?.option || [],
    task.option || [],
  ])

const handleTaskOptionUpdate = (
  taskName: string,
  payload: { optionName: string; value: MaaFWTaskOptionValue }
) => {
  taskSnapshot.value.taskOptions[taskName] ||= {}
  taskSnapshot.value.taskOptions[taskName][payload.optionName] = payload.value
  clearPreset()
}

const getTaskLabel = (taskName: string) => {
  const task = taskByName.value.get(taskName)
  return task ? getDisplayName(task) : taskName
}

const getTaskKey = (taskName: string) => taskName

const resolveAssetUrl = (path?: string | null) => buildMaaFWAssetUrl(previewData.value?.path, path)

const filterSelectOption: SelectProps['filterOption'] = (input, option) =>
  String(option?.label || '')
    .toLowerCase()
    .includes(input.toLowerCase())

onMounted(() => {
  void reloadInterface(false)
  void refreshMxuImportAvailability()
})
</script>

<style scoped>
.maaend-task-editor {
  min-width: 0;
}

.editor-header,
.panel-header,
.selected-task-header,
.task-row {
  display: flex;
  align-items: center;
}

.editor-header,
.panel-header {
  justify-content: space-between;
  gap: 16px;
}

.editor-header {
  margin-bottom: 16px;
}

.editor-header h3,
.selected-task-header h4 {
  margin: 0;
  color: var(--ant-color-text);
}

.project-meta,
.selected-task-header span {
  margin-top: 4px;
  color: var(--ant-color-text-secondary);
  font-size: 12px;
}

.project-meta span {
  margin-left: 8px;
}

.editor-state {
  display: flex;
  min-height: 160px;
  align-items: center;
  justify-content: center;
}

.context-row {
  margin-bottom: 8px;
}

.task-layout {
  align-items: stretch;
}

.panel-header {
  margin-bottom: 12px;
  font-weight: 600;
}

.add-task-select {
  width: min(240px, 65%);
}

.task-list,
.option-panel {
  min-height: 280px;
  max-height: 560px;
  overflow: auto;
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 8px;
  background: var(--ant-color-bg-container);
}

.task-list {
  padding: 8px;
}

.task-row {
  gap: 10px;
  min-height: 44px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.task-row:hover,
.task-row-selected {
  background: var(--ant-color-fill-secondary);
}

.task-row-ghost {
  opacity: 0.45;
}

.drag-handle {
  color: var(--ant-color-text-tertiary);
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.task-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.task-name {
  min-width: 0;
  flex: 1;
  overflow-wrap: anywhere;
}

.task-empty {
  min-height: 280px;
  padding-top: 72px;
  border: 1px solid var(--ant-color-border-secondary);
  border-radius: 8px;
}

.option-panel {
  padding: 16px;
}

.selected-task-header {
  justify-content: space-between;
  margin-bottom: 12px;
}

.task-description {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ant-color-border-secondary);
}

.import-warning {
  margin-top: 16px;
}

@media (max-width: 991px) {
  .option-panel {
    margin-top: 16px;
  }
}

@media (max-width: 576px) {
  .editor-header,
  .panel-header {
    align-items: stretch;
    flex-direction: column;
  }

  .add-task-select {
    width: 100%;
  }
}
</style>
