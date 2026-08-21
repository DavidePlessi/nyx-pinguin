<script setup lang="ts">
import { t } from '../i18n'

const props = defineProps({
  show: Boolean,
  title: { type: String },
  message: String,
  isConfirm: Boolean,
  hasInput: Boolean,
  modelValue: String
})

const emit = defineEmits(['confirm', 'cancel', 'update:modelValue'])

const onConfirm = () => emit('confirm')
const onCancel = () => emit('cancel')
const updateValue = (e: Event) => {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm transition-opacity">
      <div class="glass-panel p-6 max-w-md w-full border-t-4 border-cyber-cyan shadow-[0_0_20px_rgba(0,255,255,0.2)]">
        <h3 class="font-orbitron text-xl text-cyber-cyan mb-4 flex items-center gap-2 uppercase">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          {{ title || t('modal.systemAlert') }}
        </h3>
        <p class="font-rajdhani text-gray-300 text-lg mb-6">
          {{ message }}
        </p>
        
        <div v-if="hasInput" class="mb-8">
          <input 
            type="text" 
            :value="modelValue" 
            @input="updateValue"
            class="neon-input w-full" 
            placeholder="Inserisci link..." 
            @keyup.enter="onConfirm"
          />
        </div>

        <div class="flex justify-end gap-4">
          <button v-if="isConfirm" @click="onCancel" class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 font-orbitron text-sm rounded border border-gray-600 transition-colors">
            {{ t('modal.abort') }}
          </button>
          <button @click="onConfirm" class="px-6 py-2 bg-cyber-purple/20 hover:bg-cyber-purple/40 text-cyber-purple border border-cyber-purple font-orbitron text-sm rounded transition-all shadow-[0_0_10px_rgba(188,19,254,0.3)]">
            {{ isConfirm ? t('modal.confirm') : t('modal.acknowledge') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
