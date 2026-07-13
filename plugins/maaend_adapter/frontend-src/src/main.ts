import Antd from "ant-design-vue";
import { defineCustomElement } from "vue";

import MaaEndTaskEditorElement from "./MaaEndTaskEditorElement.ce.vue";

const MaaEndTaskEditor = defineCustomElement(MaaEndTaskEditorElement, {
  configureApp(app) {
    app.use(Antd);
  },
  shadowRoot: false,
});

if (!customElements.get("maaend-task-editor")) {
  customElements.define("maaend-task-editor", MaaEndTaskEditor);
}
