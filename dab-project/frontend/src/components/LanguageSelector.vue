<script setup lang="ts">
import { currentLocale, setLanguage } from '../i18n'

const languages = [
  { code: 'en', label: 'EN' },
  { code: 'it', label: 'IT' },
  { code: 'es', label: 'ES' },
  { code: 'fr', label: 'FR' },
  { code: 'de', label: 'DE' }
]
</script>

<template>
  <div class="flex gap-2 text-sm font-rajdhani bg-black/60 backdrop-blur-md p-1.5 rounded-lg border border-gray-800/50 shadow-lg">
    <button 
      v-for="lang in languages" 
      :key="lang.code"
      @click="setLanguage(lang.code)"
      :class="[
        'px-2 py-1 border rounded transition-colors',
        currentLocale === lang.code 
          ? 'border-cyber-cyan text-cyber-cyan bg-cyber-cyan/10' 
          : 'border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-500 bg-black/40'
      ]"
    >
      {{ lang.label }}
    </button>
  </div>
</template>
