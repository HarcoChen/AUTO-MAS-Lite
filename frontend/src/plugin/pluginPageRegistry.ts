import { shallowRef } from 'vue'

import type { PageDeclaration } from '@/router/pageDeclarations'

const pluginPages = shallowRef<PageDeclaration[]>([])

export function setPluginPages(pages: PageDeclaration[]): void {
  pluginPages.value = pages
}

export function usePluginPages() {
  return pluginPages
}
