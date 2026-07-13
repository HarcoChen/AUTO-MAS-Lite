<template>
  <a-spin v-if="loading" tip="正在加载插件编辑器" />
  <a-alert
    v-else-if="errorMessage"
    type="warning"
    show-icon
    message="插件编辑器加载失败"
    :description="errorMessage"
  />
  <component
    :is="elementTag"
    v-else-if="elementTag"
    ref="elementRef"
    @model-change="handleModelChange"
  />
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import { ensurePluginFrontendPage } from '@/plugin/pluginFrontendLoader'
import { usePluginPages } from '@/plugin/pluginPageRegistry'

const props = defineProps<{
  pageId: string
  modelValue?: unknown
  properties?: Record<string, unknown>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
}>()

const pages = usePluginPages()
const loading = ref(true)
const errorMessage = ref('')
const elementRef = ref<HTMLElement | null>(null)
const page = computed(() => pages.value.find(item => item.id === props.pageId) || null)
const elementTag = computed(() => page.value?.element_tag || '')

const syncProperties = async () => {
  await nextTick()
  const element = elementRef.value as (HTMLElement & Record<string, unknown>) | null
  if (!element) return
  element.modelValue = props.modelValue
  for (const [key, value] of Object.entries(props.properties || {})) {
    element[key] = value
  }
}

const loadElement = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    if (!page.value) {
      throw new Error(`未找到插件前端声明: ${props.pageId}`)
    }
    await ensurePluginFrontendPage(page.value)
    await syncProperties()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error)
  } finally {
    loading.value = false
  }
}

const handleModelChange = (event: Event) => {
  const detail = (event as CustomEvent).detail
  emit('update:modelValue', Array.isArray(detail) ? detail[0] : detail)
}

watch(page, () => void loadElement(), { immediate: true })
watch(() => props.modelValue, syncProperties, { deep: true })
watch(() => props.properties, syncProperties, { deep: true })
</script>
