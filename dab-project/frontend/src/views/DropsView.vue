<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

import QuestlogItemSelector from '../components/QuestlogItemSelector.vue'
import CyberModal from '../components/CyberModal.vue'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))

const userGuilds = ref<string[]>([])
const userGuildsInfo = ref<any[]>([])
const selectedGuild = ref<string>('')
const buildStatus = ref<string>('Nessuna build')

const characterName = ref<string>('')
const playStyle = ref<string>('')
const questlogUrl = ref<string>('')

const classMappings = ref<any[]>([])

const characterClass = computed(() => {
  if (slots.value.main_weapon && slots.value.secondary_weapon) {
    const w1 = (slots.value.main_weapon.subCategory || '').toLowerCase()
    const w2 = (slots.value.secondary_weapon.subCategory || '').toLowerCase()
    const match = classMappings.value.find(m => 
      (m.weapon_1 === w1 && m.weapon_2 === w2) || (m.weapon_1 === w2 && m.weapon_2 === w1)
    )
    if (match) return match.class_name
  }
  return ''
})

const slots = ref<any>({
  main_weapon: null,
  secondary_weapon: null,
  belt: null,
  necklace: null,
  bracelet: null,
  ring_1: null,
  ring_2: null,
  brooch: null,
  cloak: null,
  legs: null,
  hands: null,
  feet: null,
  head: null,
  chest: null
})

const isLoading = ref(false)
const error = ref('')

// Modal State
const modalState = ref({
  show: false,
  title: 'SYSTEM ALERT',
  message: '',
  isConfirm: false,
  hasInput: false,
  inputValue: '',
  resolve: null as ((value: any) => void) | null
})

const showAlert = (message: string, title = 'SYSTEM ALERT') => {
  modalState.value = {
    show: true,
    title,
    message,
    isConfirm: false,
    hasInput: false,
    inputValue: '',
    resolve: null
  }
}

const promptAlert = (message: string, title = 'INPUT REQUIRED'): Promise<string | null> => {
  return new Promise((resolve) => {
    modalState.value = {
      show: true,
      title,
      message,
      isConfirm: true,
      hasInput: true,
      inputValue: '',
      resolve
    }
  })
}

const handleModalConfirm = () => {
  if (modalState.value.resolve) {
    modalState.value.resolve(modalState.value.hasInput ? modalState.value.inputValue : true)
  }
  modalState.value.show = false
}

const handleModalCancel = () => {
  if (modalState.value.resolve) {
    modalState.value.resolve(modalState.value.hasInput ? null : false)
  }
  modalState.value.show = false
}

const fetchMyBuild = async () => {
  if (!selectedGuild.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${selectedGuild.value}/builds`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      const build = await res.json()
      if (build && build.slots) {
        slots.value = { ...slots.value, ...build.slots }
        buildStatus.value = build.status
        characterName.value = build.character_name || ''
        playStyle.value = build.play_style || ''
        questlogUrl.value = build.questlog_url || ''
      } else {
        buildStatus.value = 'Nessuna build'
        characterName.value = ''
        playStyle.value = ''
        questlogUrl.value = ''
        // reset slots
        for(const k in slots.value) slots.value[k] = null
      }
    }
  } catch(e: any) {
    error.value = t('drops.errorLoadingBuild')
  } finally {
    isLoading.value = false
  }
}

const saveBuild = async (showSuccessAlert = true) => {
  if (!selectedGuild.value) return false
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${selectedGuild.value}/builds`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${sessionToken.value}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        slots: slots.value,
        character_name: characterName.value,
        play_style: playStyle.value,
        questlog_url: questlogUrl.value
      })
    })
    if (res.ok) {
      const data = await res.json()
      buildStatus.value = data.status
      if (showSuccessAlert) {
        showAlert(t('drops.buildSavedAsDraft'), "SUCCESS")
      }
      return true
    } else {
      error.value = t('drops.errorSavingBuild')
      return false
    }
  } catch(e: any) {
    error.value = e.message
    return false
  } finally {
    isLoading.value = false
  }
}

const submitBuild = async () => {
  const saved = await saveBuild(false)
  if (!saved) return

  if (!selectedGuild.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${selectedGuild.value}/builds/submit`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      const data = await res.json()
      buildStatus.value = data.status
      showAlert(t('drops.buildSubmittedForApproval'), "SUCCESS")
    } else {
      error.value = t('drops.errorSubmittingBuild')
    }
  } catch(e: any) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

const isImporting = ref(false)

const importFromQuestlog = async () => {
  const url = await promptAlert("Inserisci il link della build di Questlog (es: https://questlog.gg/throne-and-liberty/en/character-builder/slug):", "IMPORTA DA QUESTLOG")
  if (!url) return
  
  isImporting.value = true
  error.value = ''
  try {
    const res = await fetch(`${BACKEND_URL}/api/questlog/import-build?url=${encodeURIComponent(url)}`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    
    if (res.ok) {
      const data = await res.json()
      // Overwrite the mapped slots
      for (const k in slots.value) {
        slots.value[k] = data.slots[k] || null
      }
      questlogUrl.value = url
      showAlert("Build importata con successo! Clicca su Salva per applicare le modifiche.", "SUCCESS")
    } else {
      const errData = await res.json()
      error.value = errData.detail || "Errore durante l'importazione"
      showAlert(error.value, "ERRORE")
    }
  } catch (err: any) {
    error.value = err.message
    showAlert("Errore di rete durante l'importazione", "ERRORE")
  } finally {
    isImporting.value = false
  }
}

onMounted(() => {
  if (sessionToken.value) {
    try {
      JSON.parse(atob(sessionToken.value.split('.')[1]))
      // userGuilds... we don't have them in token! We should fetch /api/drops/me
      fetch(`${BACKEND_URL}/api/drops/me`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } })
        .then(res => res.json())
        .then(user => {
          userGuilds.value = user.guilds || []
          userGuildsInfo.value = user.guilds_info || []
          if (userGuilds.value.length > 0) {
            selectedGuild.value = userGuilds.value[0]
            fetchMyBuild()
          }
        })

      // Fetch classes
      fetch(`${BACKEND_URL}/api/drops/classes`)
        .then(res => res.json())
        .then(data => {
          classMappings.value = data
        })
        .catch(err => console.error("Failed to load classes", err))
        
    } catch(e){}
  }
})

</script>

<template>
  <div class="p-4 md:p-8 max-w-6xl mx-auto animate-fade-in">
    
    <!-- CyberModal -->
    <CyberModal 
      :show="modalState.show" 
      :title="modalState.title" 
      :message="modalState.message" 
      :is-confirm="modalState.isConfirm"
      :has-input="modalState.hasInput"
      v-model="modalState.inputValue"
      @confirm="handleModalConfirm"
      @cancel="handleModalCancel"
    />

    <div class="flex justify-between items-center mb-6">
      <h2 class="font-rajdhani text-3xl font-bold neon-text-cyan">{{ t('drops.myBuilds') }}</h2>
      <router-link to="/" class="text-sm text-cyber-cyan hover:text-white transition-colors whitespace-nowrap font-bold flex items-center gap-1">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
        {{ t('app.backToHub') }}
      </router-link>
    </div>
    
    <div class="mb-6">
      <label class="block text-gray-400 font-rajdhani mb-2">{{ t('drops.selectGuild') }}</label>
      <select v-model="selectedGuild" @change="fetchMyBuild" class="neon-input bg-gray-900 w-full max-w-md">
        <option v-for="g in userGuildsInfo" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
    </div>

    <!-- Character Info -->
    <div v-if="selectedGuild" class="bg-gray-900/50 border border-gray-800 rounded-lg p-4 sm:p-6 mb-6">
      <h3 class="text-xl font-rajdhani font-bold text-cyber-purple mb-6 uppercase">{{ t('drops.characterInfo') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label class="block text-gray-400 font-rajdhani mb-2">{{ t('drops.characterName') }}</label>
          <input type="text" v-model="characterName" class="neon-input" :placeholder="t('drops.characterNamePlaceholder')" />
        </div>
        <div>
          <label class="block text-gray-400 font-rajdhani mb-2">{{ t('drops.characterClass') }}</label>
          <input type="text" :value="characterClass" class="neon-input text-gray-500 cursor-not-allowed" :placeholder="t('drops.characterClassPlaceholder')" disabled />
        </div>
        <div>
          <label class="block text-gray-400 font-rajdhani mb-2">{{ t('drops.playStyle') }}</label>
          <select v-model="playStyle" class="neon-input">
            <option value="" disabled>{{ t('drops.selectPlayStyle') }}</option>
            <option value="PvP">{{ t('drops.pvp') }}</option>
            <option value="PvE">{{ t('drops.pve') }}</option>
            <option value="PvPxPvE">{{ t('drops.pvpxpve') }}</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="selectedGuild" class="bg-gray-900/50 border border-gray-800 rounded-lg p-4 sm:p-6">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div class="flex items-center gap-4">
          <h3 class="text-xl font-rajdhani font-bold text-gray-200">{{ t('drops.mainEquipment') }}</h3>
          <button @click="importFromQuestlog" :disabled="isImporting" class="bg-indigo-900/50 hover:bg-indigo-800 text-indigo-300 text-xs font-bold py-1.5 px-3 rounded border border-indigo-700 transition-colors flex items-center gap-2">
            <svg v-if="isImporting" class="animate-spin h-3 w-3 text-indigo-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            {{ isImporting ? 'Importazione...' : 'Importa da Questlog' }}
          </button>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm font-mono text-gray-400">{{ t('drops.status') }}</span>
          <span class="px-3 py-1 rounded font-bold text-xs uppercase" 
            :class="{
              'bg-gray-700 text-gray-300': buildStatus === 'Nessuna build' || buildStatus === 'draft' || buildStatus === 'No build' || buildStatus === 'Sin build' || buildStatus === 'Pas de build' || buildStatus === 'Kein Build',
              'bg-yellow-900 text-yellow-300': buildStatus === 'pending',
              'bg-green-900 text-green-300': buildStatus === 'primary'
            }">
            <template v-if="buildStatus === 'Nessuna build' || buildStatus === 'No build' || buildStatus === 'Sin build' || buildStatus === 'Pas de build' || buildStatus === 'Kein Build'">{{ t('drops.statusNoBuild') }}</template>
            <template v-else>{{ buildStatus }}</template>
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <QuestlogItemSelector v-model="slots.main_weapon" label="Main Weapon" mainCategory="weapons" subCategory="" />
        <QuestlogItemSelector v-model="slots.secondary_weapon" label="Secondary Weapon" mainCategory="weapons" subCategory="" />
        
        <QuestlogItemSelector v-model="slots.chest" label="Chest" mainCategory="armor" subCategory="chest" />
        <QuestlogItemSelector v-model="slots.legs" label="Legs" mainCategory="armor" subCategory="legs" />
        <QuestlogItemSelector v-model="slots.head" label="Head" mainCategory="armor" subCategory="head" />
        <QuestlogItemSelector v-model="slots.hands" label="Hands" mainCategory="armor" subCategory="hands" />
        <QuestlogItemSelector v-model="slots.feet" label="Feet" mainCategory="armor" subCategory="feet" />
        <QuestlogItemSelector v-model="slots.cloak" label="Cloak" mainCategory="armor" subCategory="cloak" />
        
        <QuestlogItemSelector v-model="slots.necklace" label="Necklace" mainCategory="accessories" subCategory="necklace" />
        <QuestlogItemSelector v-model="slots.bracelet" label="Bracelet" mainCategory="accessories" subCategory="bracelet" />
        <QuestlogItemSelector v-model="slots.ring_1" label="Ring 1" mainCategory="accessories" subCategory="ring" />
        <QuestlogItemSelector v-model="slots.ring_2" label="Ring 2" mainCategory="accessories" subCategory="ring" />
        <QuestlogItemSelector v-model="slots.belt" label="Belt" mainCategory="accessories" subCategory="belt" />
        <QuestlogItemSelector v-model="slots.brooch" label="Brooch" mainCategory="accessories" subCategory="brooch" />
      </div>

      <div class="mt-8 flex flex-col sm:flex-row justify-end gap-4 border-t border-gray-800 pt-6">
        <button @click="saveBuild(true)" class="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded transition-colors w-full sm:w-auto">
          {{ t('drops.saveDraft') }}
        </button>
        <button @click="submitBuild" :disabled="buildStatus === 'pending' || buildStatus === 'primary'" class="neon-btn-primary px-8 w-full sm:w-auto">
          {{ t('drops.submitForApproval') }}
        </button>
      </div>
      <p v-if="error" class="text-red-400 mt-4 text-right">{{ error }}</p>
    </div>
  </div>
</template>
