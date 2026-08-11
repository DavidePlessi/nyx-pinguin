<script setup lang="ts">
const props = defineProps({
  show: Boolean,
  title: { type: String, default: "SYSTEM ALERT" },
  message: String,
  isConfirm: Boolean
})

const emit = defineEmits(['confirm', 'cancel'])

const onConfirm = () => emit('confirm')
const onCancel = () => emit('cancel')
</script>

<template>
  <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm transition-opacity">
    <div class="glass-panel p-6 max-w-md w-full border-t-4 border-cyber-cyan shadow-[0_0_20px_rgba(0,255,255,0.2)]">
      <h3 class="font-orbitron text-xl text-cyber-cyan mb-4 flex items-center gap-2 uppercase">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        {{ title }}
      </h3>
      <p class="font-rajdhani text-gray-300 text-lg mb-8">
        {{ message }}
      </p>
      
      <div class="flex justify-end gap-4">
        <button v-if="isConfirm" @click="onCancel" class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 font-orbitron text-sm rounded border border-gray-600 transition-colors">
          ABORT
        </button>
        <button @click="onConfirm" class="px-6 py-2 bg-cyber-purple/20 hover:bg-cyber-purple/40 text-cyber-purple border border-cyber-purple font-orbitron text-sm rounded transition-all shadow-[0_0_10px_rgba(188,19,254,0.3)]">
          {{ isConfirm ? 'CONFIRM' : 'ACKNOWLEDGE' }}
        </button>
      </div>
    </div>
  </div>
</template>
