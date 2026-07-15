import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
//
// The demo can render EITHER your local component source or the published
// @staski/panel-map package, selected by Vite's --mode:
//   * default (dev / build)      -> LOCAL source  (src/PanelMap/PanelMap.vue) — playground
//   * --mode published           -> the installed @staski/panel-map package  — consumer path
// See the dev / dev:published / build / build:published scripts in package.json.
export default defineConfig(({ mode }) => {
  const alias = {
    '@': fileURLToPath(new URL('./src', import.meta.url)),
  }
  if (mode !== 'published') {
    alias['@staski/panel-map'] =
      fileURLToPath(new URL('./src/PanelMap/PanelMap.vue', import.meta.url))
  }
  return {
    plugins: [vue()],
    resolve: { alias },
  }
})
