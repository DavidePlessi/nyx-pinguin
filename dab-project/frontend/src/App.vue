<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <!-- Header -->
    <header class="text-center mb-12">
      <h1 class="font-orbitron font-black text-5xl neon-text-purple tracking-widest mb-2 uppercase">
        Nyx Pinguin
      </h1>
      <p class="font-rajdhani text-2xl text-cyber-cyan tracking-wide">
        // AUDIO BROADCASTING MATRIX
      </p>
      
      <div class="mt-4 no-print" v-if="route.name !== 'Manual' && route.name !== 'Login'">
        <router-link :to="{ name: 'Manual', query: route.query }" class="inline-block text-sm font-rajdhani text-gray-400 hover:text-cyber-cyan border border-gray-700 hover:border-cyber-cyan px-4 py-1 rounded transition-colors">
          [ VISUALIZZA MANUALE OPERATIVO ]
        </router-link>
      </div>
    </header>

    <!-- Main Content Wrapped by Vue Router -->
    <router-view />
  </div>
</template>
