import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vue from "../../../frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { defineConfig } from "../../../frontend/node_modules/vite/dist/node/index.js";

const rootDir = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(rootDir, "../src/maaend_adapter/frontend/dist");

function pluginVueRuntimeExternal() {
  function transformVueImportSpecifiers(specifiers) {
    const bindings = specifiers
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => {
        const aliasMatch = item.match(
          /^([A-Za-z_$][\w$]*)\s+as\s+([A-Za-z_$][\w$]*)$/,
        );
        return aliasMatch ? `${aliasMatch[1]}: ${aliasMatch[2]}` : item;
      });
    return `const { ${bindings.join(", ")} } = window.__AUTO_MAS_PLUGIN_VUE__ || {};`;
  }

  return {
    name: "auto-mas-plugin-vue-runtime-external",
    enforce: "post",
    generateBundle(_options, bundle) {
      for (const chunk of Object.values(bundle)) {
        if (chunk.type !== "chunk") continue;
        chunk.code = chunk.code
          .replace(
            /import\s+([A-Za-z_$][\w$]*)\s*,\s*\{\s*([^}]+)\s*\}\s*from\s*["']vue["'];?\n?/g,
            (_match, defaultBinding, specifiers) =>
              `const ${defaultBinding} = window.__AUTO_MAS_PLUGIN_VUE__ || {};\n${transformVueImportSpecifiers(specifiers)}\n`,
          )
          .replace(
            /import\s*\{\s*([^}]+)\s*\}\s*from\s*["']vue["'];?\n?/g,
            (_match, specifiers) =>
              `${transformVueImportSpecifiers(specifiers)}\n`,
          )
          .replace(
            /import\s+([A-Za-z_$][\w$]*)\s+from\s*["']vue["'];?\n?/g,
            (_match, defaultBinding) =>
              `const ${defaultBinding} = window.__AUTO_MAS_PLUGIN_VUE__ || {};\n`,
          )
          .replace(/import\s+["']vue["'];?\n?/g, "");
      }
    },
  };
}

export default defineConfig(({ command }) => ({
  root: rootDir,
  plugins: [vue({ customElement: true }), pluginVueRuntimeExternal()],
  resolve: {
    alias: {
      "@": resolve(rootDir, "../../../frontend/src"),
      "ant-design-vue": resolve(
        rootDir,
        "../../../frontend/node_modules/ant-design-vue",
      ),
      "@ant-design/icons-vue": resolve(
        rootDir,
        "../../../frontend/node_modules/@ant-design/icons-vue",
      ),
      vuedraggable: resolve(
        rootDir,
        "../../../frontend/node_modules/vuedraggable/dist/vuedraggable.umd.js",
      ),
      vue: resolve(
        rootDir,
        "../../../frontend/node_modules/vue/dist/vue.runtime.esm-bundler.js",
      ),
    },
  },
  build: {
    outDir: outputDir,
    emptyOutDir: true,
    target: "es2020",
    cssCodeSplit: false,
    lib: {
      entry: resolve(rootDir, "src/main.ts"),
      formats: ["es"],
      fileName: () => "index.js",
    },
    rollupOptions: {
      external: command === "build" ? ["vue"] : [],
    },
  },
}));
