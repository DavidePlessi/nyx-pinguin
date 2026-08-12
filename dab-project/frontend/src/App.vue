<script setup lang="ts">
import { useRoute } from 'vue-router'
import { t } from './i18n'
import LanguageSelector from './components/LanguageSelector.vue'

const route = useRoute()
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl relative">
    <!-- Language Selector -->
    <div class="flex justify-center md:absolute md:top-8 md:right-8 mb-8 md:mb-0 no-print z-50">
      <LanguageSelector />
    </div>

    <!-- Header -->
    <header class="text-center mb-12 relative">
      <h1 class="font-orbitron font-black text-4xl md:text-5xl neon-text-purple tracking-widest mb-2 uppercase">
        Nyx Pinguin
      </h1>
      <p class="font-rajdhani text-xl md:text-2xl text-cyber-cyan tracking-wide">
        {{ t('app.audioMatrix') }}
      </p>
      
      <div class="mt-4 no-print" v-if="route.name !== 'Manual' && route.name !== 'Login'">
        <router-link :to="{ name: 'Manual', query: route.query }" class="inline-block text-sm font-rajdhani text-gray-400 hover:text-cyber-cyan border border-gray-700 hover:border-cyber-cyan px-4 py-1 rounded transition-colors">
          {{ t('app.viewManual') }}
        </router-link>
      </div>
    </header>

    <!-- Main Content Wrapped by Vue Router -->
    <router-view />

    <!-- Footer -->
    <footer class="mt-16 pb-6 text-center no-print flex justify-center border-t border-gray-800/50 pt-8">
      <a href="https://fiveamtech.it/?utm_source=nyx-pinguin&utm_medium=referral" target="_blank" rel="noopener noreferrer" class="inline-flex flex-col items-center gap-1 text-gray-200 hover:text-white transition-all duration-300 group hover:scale-105">
        <span class="font-orbitron font-bold text-sm tracking-[0.2em] uppercase neon-text-purple -mr-[0.2em]">{{ t('app.poweredBy') }}</span>
        <img src="https://fiveamtech.it/logo-nobg.png" alt="Five AM Tech" class="h-32 drop-shadow-[0_0_8px_rgba(0,255,255,0.5)] group-hover:drop-shadow-[0_0_15px_rgba(0,255,255,0.8)] transition-all" />
      </a>
    </footer>
  </div>
</template>
