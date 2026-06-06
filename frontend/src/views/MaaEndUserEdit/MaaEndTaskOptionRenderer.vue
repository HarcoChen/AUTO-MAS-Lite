<template>
  <div class="maaend-task-options" :class="isRoot ? 'is-root' : 'is-nested'">
    <div v-for="optName in options" :key="optName" class="option-item">
      <template v-if="optionDefinitions[optName]">
        <div class="option-header">
          <span class="option-label">{{ optionDefinitions[optName].label || optName }}</span>
          <a-tooltip v-if="optionDefinitions[optName].description" :title="optionDefinitions[optName].description">
            <QuestionCircleOutlined class="help-icon" />
          </a-tooltip>
        </div>

        <div class="option-control">
          <!-- Switch -->
          <a-switch
            v-if="optionDefinitions[optName].type === 'switch'"
            :checked="getOptionValue(optName, 'switch')"
            @change="handleSwitchChange(optName, $event)"
          />

          <!-- Select -->
          <a-select
            v-else-if="optionDefinitions[optName].type === 'select'"
            :value="getOptionValue(optName, 'select')"
            style="width: 100%"
            @change="handleSelectChange(optName, $event)"
          >
            <a-select-option
              v-for="caseItem in optionDefinitions[optName].cases || []"
              :key="caseItem.name"
              :value="caseItem.name"
            >
              {{ caseItem.label || caseItem.name }}
            </a-select-option>
          </a-select>

          <!-- Checkbox -->
          <a-checkbox-group
            v-else-if="optionDefinitions[optName].type === 'checkbox'"
            :value="getOptionValue(optName, 'checkbox')"
            @change="handleCheckboxChange(optName, $event)"
          >
            <a-checkbox
              v-for="caseItem in optionDefinitions[optName].cases || []"
              :key="caseItem.name"
              :value="caseItem.name"
            >
              {{ caseItem.label || caseItem.name }}
            </a-checkbox>
          </a-checkbox-group>

          <!-- Input -->
          <div v-else-if="optionDefinitions[optName].type === 'input'" class="input-fields">
            <div
              v-for="input in optionDefinitions[optName].inputs || []"
              :key="input.name"
              class="input-row"
            >
              <span class="input-label">{{ input.label || input.name }}</span>
              <a-input
                :value="getInputValue(optName, input.name)"
                :placeholder="String(input.default || '')"
                style="width: 100%"
                @change="handleInputChange(optName, input.name, $event.target.value)"
              />
            </div>
          </div>
        </div>

        <!-- Recursively render sub-options based on active cases -->
        <div v-if="getSubOptions(optName).length > 0" class="sub-options">
          <MaaEndTaskOptionRenderer
            :options="getSubOptions(optName)"
            :option-definitions="optionDefinitions"
            :model-value="modelValue"
            :is-root="false"
            @update:modelValue="$emit('update:modelValue', $event)"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    options: string[]
    optionDefinitions: Record<string, any>
    modelValue: Record<string, any>
    isRoot?: boolean
  }>(),
  {
    isRoot: true,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

const getOptionValue = (optName: string, type: string) => {
  const val = props.modelValue[optName]
  const def = props.optionDefinitions[optName]

  if (val && val.type === type) {
    if (type === 'switch') return val.value
    if (type === 'select') return val.caseName
    if (type === 'checkbox') return val.caseNames
  }

  // Fallback to defaults
  if (type === 'switch') {
    return def.default_case === 'Yes'
  }
  if (type === 'select') {
    return def.default_case || (def.cases && def.cases.length > 0 ? def.cases[0].name : '')
  }
  if (type === 'checkbox') {
    return Array.isArray(def.default_case) ? def.default_case : []
  }
  return null
}

const getInputValue = (optName: string, inputName: string) => {
  const val = props.modelValue[optName]
  if (val && val.type === 'input' && val.values) {
    if (val.values[inputName] !== undefined) {
      return val.values[inputName]
    }
  }
  // No default rendered as value; placeholder takes care of default display.
  return ''
}

const updateValue = (optName: string, payload: any) => {
  const newVal = { ...props.modelValue }
  newVal[optName] = payload
  
  // Clean up stale sub-options
  const allValidSubOptions = getAllValidSubOptions(props.options, newVal)
  for (const key in newVal) {
    if (!props.options.includes(key) && !allValidSubOptions.includes(key)) {
      delete newVal[key]
    }
  }

  emit('update:modelValue', newVal)
}

const handleSwitchChange = (optName: string, checked: boolean) => {
  updateValue(optName, { type: 'switch', value: checked })
}

const handleSelectChange = (optName: string, caseName: string) => {
  updateValue(optName, { type: 'select', caseName })
}

const handleCheckboxChange = (optName: string, caseNames: string[]) => {
  updateValue(optName, { type: 'checkbox', caseNames })
}

const handleInputChange = (optName: string, inputName: string, value: string) => {
  const currentVal = props.modelValue[optName]
  const values = currentVal && currentVal.type === 'input' ? { ...currentVal.values } : {}
  values[inputName] = String(value)
  updateValue(optName, { type: 'input', values })
}

const getActiveCases = (optName: string, modelVal = props.modelValue): string[] => {
  const def = props.optionDefinitions[optName]
  if (!def || !def.cases) return []

  const val = modelVal[optName]
  if (val) {
    if (val.type === 'switch') {
      const activeCase = val.value ? 'Yes' : 'No'
      return def.cases.map((c: any) => c.name).includes(activeCase) ? [activeCase] : []
    }
    if (val.type === 'select') return [val.caseName]
    if (val.type === 'checkbox') return val.caseNames
  } else {
    if (def.type === 'switch') {
      const activeCase = def.default_case === 'Yes' ? 'Yes' : 'No'
      return def.cases.map((c: any) => c.name).includes(activeCase) ? [activeCase] : []
    }
    if (def.type === 'select') {
      const activeCase = def.default_case || (def.cases && def.cases.length > 0 ? def.cases[0].name : '')
      return activeCase ? [activeCase] : []
    }
    if (def.type === 'checkbox') {
      return Array.isArray(def.default_case) ? def.default_case : []
    }
  }
  return []
}

const getSubOptions = (optName: string, modelVal = props.modelValue): string[] => {
  const activeCases = getActiveCases(optName, modelVal)
  const def = props.optionDefinitions[optName]
  if (!def || !def.cases) return []

  const subOptions: string[] = []
  for (const c of def.cases) {
    if (activeCases.includes(c.name) && c.option) {
      subOptions.push(...c.option)
    }
  }
  return subOptions
}

const getAllValidSubOptions = (rootOptions: string[], modelVal: Record<string, any>): string[] => {
  const result: string[] = []
  const traverse = (opts: string[]) => {
    for (const opt of opts) {
      const subs = getSubOptions(opt, modelVal)
      result.push(...subs)
      traverse(subs)
    }
  }
  traverse(rootOptions)
  return result
}
</script>

<style scoped>
.maaend-task-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.maaend-task-options.is-root {
  padding: 16px;
  background: var(--ant-color-fill-quaternary);
  border-radius: 8px;
  margin-top: 12px;
}

.maaend-task-options.is-nested {
  gap: 12px;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--ant-color-text);
}

.help-icon {
  color: var(--ant-color-text-tertiary);
  cursor: help;
}

.option-control {
  display: flex;
  align-items: center;
}

.input-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-label {
  min-width: 80px;
  font-size: 14px;
  color: var(--ant-color-text-secondary);
}

.sub-options {
  position: relative;
  margin-top: 4px;
  margin-left: 6px;
  padding-left: 16px;
  border-left: 2px solid var(--ant-color-primary-bg);
  border-radius: 2px;
  transition: all 0.3s ease;
}

.sub-options:hover {
  border-left-color: var(--ant-color-primary);
}
</style>
