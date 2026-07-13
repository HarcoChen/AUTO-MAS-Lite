<template>
  <MaaEndTaskEditor
    :model-value="normalizedModel"
    :project-path="projectPath"
    :controller-type="controllerType"
    @update:model-value="handleModelChange"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { MaaFWTaskSnapshot } from "@/types/script";
import MaaEndTaskEditor from "@/views/MaaEndUserEdit/MaaEndTaskEditor.vue";

interface EditorModel {
  controller: string;
  resource: string;
  selectedPreset: string;
  taskSnapshot: string | MaaFWTaskSnapshot;
}

const props = withDefaults(
  defineProps<{
    modelValue?: EditorModel;
    projectPath?: string;
    controllerType?: "Win32" | "Adb";
  }>(),
  {
    projectPath: "",
    controllerType: "Win32",
  },
);

const emit = defineEmits<{
  "model-change": [value: EditorModel];
}>();

const normalizedModel = computed<EditorModel>(
  () =>
    props.modelValue || {
      controller: "",
      resource: "",
      selectedPreset: "",
      taskSnapshot: "{}",
    },
);

const handleModelChange = (value: EditorModel) => {
  emit("model-change", value);
};
</script>
