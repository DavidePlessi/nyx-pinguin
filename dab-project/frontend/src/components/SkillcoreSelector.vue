<script setup lang="ts">
import { ref, watch } from 'vue'
import { t } from '../i18n'

const props = defineProps<{
  modelValue: any // Oggetto item o null
  slotCategory: string // "Weapon" or "Armor / Acc."
  weapons: string[] // List of valid weapon classes, e.g. ["sword2h", "dagger"]
  label: string
}>()

const emit = defineEmits(['update:modelValue'])

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const searchQuery = ref(props.modelValue ? props.modelValue.name : '')
const results = ref<any[]>([])
const isSearching = ref(false)
const showDropdown = ref(false)
let debounceTimeout: any = null

const searchItems = async (query: string) => {
  if (!query || query.length < 2) {
    results.value = []
    return
  }
  isSearching.value = true
  try {
    const url = new URL(`${BACKEND_URL}/api/drops/skillcores`)
    url.searchParams.append('query', query)
    url.searchParams.append('slot', props.slotCategory)
    if (props.slotCategory === 'Weapon' && props.weapons && props.weapons.length > 0) {
      props.weapons.forEach(w => url.searchParams.append('weapons', w))
    }

    const res = await fetch(url.toString())
    if (res.ok) {
      const data = await res.json()
      results.value = data
    }
  } catch (e) {
    console.error("Errore ricerca skillcore:", e)
  } finally {
    isSearching.value = false
  }
}

const onInput = (e: any) => {
  searchQuery.value = e.target.value
  showDropdown.value = true
  if (debounceTimeout) clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    searchItems(searchQuery.value)
  }, 300)
}

const selectItem = (item: any) => {
  searchQuery.value = item.name
  showDropdown.value = false
  emit('update:modelValue', {
    id: item.id,
    name: item.name,
    icon: item.imageUrl
  })
}

// Quando arriva un nuovo modelValue dall'esterno (es. caricamento)
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    searchQuery.value = newVal.name
  } else {
    searchQuery.value = ''
  }
})

</script>

<template>
  <div class="relative w-full">
    <label class="block font-rajdhani text-gray-400 mb-1 text-sm uppercase tracking-wide">{{ label }}</label>
    <div class="flex gap-2 items-center">
      <div v-if="modelValue && modelValue.icon" class="w-10 h-10 bg-gray-800 rounded border border-gray-700 flex-shrink-0 overflow-hidden">
        <img :src="modelValue.icon" class="w-full h-full object-cover" @error="($event.target as HTMLImageElement).src=''" />
      </div>      
      <div class="relative flex-1">
        <input 
          type="text" 
          :value="searchQuery" 
          @input="onInput"
          @focus="searchQuery.length >= 2 ? showDropdown = true : null"
          class="neon-input w-full bg-gray-900" 
          :placeholder="t('drops.searchPlaceholder').replace('{label}', label)"
        >
        <!-- Dropdown -->
        <div v-if="showDropdown && (results.length > 0 || isSearching)" class="absolute z-50 w-full mt-1 bg-gray-900 border border-cyber-purple rounded shadow-xl max-h-60 overflow-y-auto custom-scrollbar">
          <div v-if="isSearching" class="p-3 text-center text-gray-400 font-mono text-sm">{{ t('drops.searching') }}</div>
          <div 
            v-for="item in results" 
            :key="item.id" 
            @click="selectItem(item)"
            class="flex items-center gap-3 p-2 hover:bg-gray-800 cursor-pointer border-b border-gray-800 last:border-0"
          >
            <img :src="item.imageUrl" class="w-8 h-8 rounded" @error="($event.target as HTMLImageElement).src=''" />
            <span class="text-gray-300 font-mono text-sm">{{ item.name }}</span>
          </div>
        </div>
      </div>
      <!-- Tasto pulisci -->
      <button v-if="modelValue" @click="emit('update:modelValue', null); searchQuery=''" class="text-red-500 hover:text-red-400 px-2 font-bold">X</button>
    </div>
  </div>
</template>
