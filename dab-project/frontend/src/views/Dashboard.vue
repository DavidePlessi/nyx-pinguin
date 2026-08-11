<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CyberModal from '../components/CyberModal.vue'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()
const route = useRoute()

const isLoading = ref(false)
const error = ref('')

const guildId = ref('')
const sourceChannelId = ref('')
const sourceRoleId = ref('')
const destChannels = ref<string[]>([])
const isActive = ref(false)

const availableChannels = ref<any[]>([])
const availableRoles = ref<any[]>([])
const logs = ref<any[]>([])
const showLogs = ref(false)
let logsInterval: any = null

const modalState = ref({
  show: false,
  title: 'SYSTEM ALERT',
  message: '',
  isConfirm: false,
  resolve: null as ((value: boolean) => void) | null
})

const showAlert = (message: string, title = 'SYSTEM ALERT') => {
  return new Promise<boolean>((resolve) => {
    modalState.value = { show: true, title, message, isConfirm: false, resolve }
  })
}

const showConfirm = (message: string, title = 'CONFIRM ACTION') => {
  return new Promise<boolean>((resolve) => {
    modalState.value = { show: true, title, message, isConfirm: true, resolve }
  })
}

const handleModalConfirm = () => {
  if (modalState.value.resolve) modalState.value.resolve(true)
  modalState.value.show = false
}

const handleModalCancel = () => {
  if (modalState.value.resolve) modalState.value.resolve(false)
  modalState.value.show = false
}

const logout = () => {
  localStorage.removeItem('dab_session_token')
  sessionToken.value = null
  if (logsInterval) clearInterval(logsInterval)
  router.replace({ name: 'Login', query: { guild: route.query.guild } })
}

const fetchDiscordData = async () => {
  try {
    const [chRes, roRes] = await Promise.all([
      fetch(`${BACKEND_URL}/api/discord/guilds/${guildId.value}/channels`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } }),
      fetch(`${BACKEND_URL}/api/discord/guilds/${guildId.value}/roles`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } })
    ])
    if (chRes.ok) availableChannels.value = await chRes.json()
    if (roRes.ok) availableRoles.value = await roRes.json()
  } catch (e) {
    console.error("Failed to fetch discord data", e)
  }
}

const loadConfig = async () => {
  if (!guildId.value) return
  
  // Sincronizza il query param quando l'utente clicca SCAN
  if (route.query.guild !== guildId.value && route.query.id !== guildId.value) {
    router.replace({ query: { ...route.query, guild: guildId.value } })
  }

  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/config/${guildId.value}`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) logout()
      throw new Error("Errore nel caricamento")
    }
    const data = await res.json()
    sourceChannelId.value = data.source_channel_id || ''
    sourceRoleId.value = data.source_role_id || ''
    destChannels.value = data.dest_channels || []
    isActive.value = data.is_active || false

    await fetchDiscordData()
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const toggleLogs = () => {
  showLogs.value = !showLogs.value
  if (showLogs.value) {
    fetchLogs()
    logsInterval = setInterval(fetchLogs, 2000)
  } else {
    if (logsInterval) clearInterval(logsInterval)
  }
}

const fetchLogs = async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/api/logs`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      logs.value = await res.json()
    }
  } catch (e) {
    console.error("Failed to fetch logs", e)
  }
}

const saveConfig = async () => {
  if (!guildId.value || !sourceChannelId.value) {
    error.value = "Guild ID e Source Channel sono obbligatori!"
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  const payload = {
    guild_id: guildId.value,
    source_channel_id: sourceChannelId.value,
    source_role_id: sourceRoleId.value || null,
    dest_channels: destChannels.value,
    is_active: isActive.value
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionToken.value}`
      },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) logout()
      throw new Error("Salvataggio fallito")
    }
    await showAlert("Configurazione salvata nel mainframe!", "SUCCESS")
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const restartSystem = async () => {
  if (!(await showConfirm("Sei sicuro di voler riavviare il bot e le API? Questo comporterà una breve interruzione del servizio.", "SYSTEM REBOOT"))) return
  
  isLoading.value = true
  error.value = ''
  try {
    const res = await fetch(`${BACKEND_URL}/api/system/restart`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken.value}`
      }
    })
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) logout()
      throw new Error("Riavvio fallito")
    }
    await showAlert("Riavvio in corso. Ricarica la pagina tra qualche secondo.", "REBOOTING")
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  const guildParam = route.query.guild || route.query.id
  if (guildParam) {
    guildId.value = guildParam as string
    if (sessionToken.value) {
      loadConfig()
    }
  }
})

onUnmounted(() => {
  if (logsInterval) clearInterval(logsInterval)
})
</script>

<template>
  <div class="glass-panel p-8">
    <CyberModal 
      :show="modalState.show" 
      :title="modalState.title" 
      :message="modalState.message" 
      :isConfirm="modalState.isConfirm"
      @confirm="handleModalConfirm"
      @cancel="handleModalCancel"
    />
    
    <div class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
      <h2 class="font-rajdhani text-3xl font-bold neon-text-cyan">MATRIX CONFIGURATION</h2>
      <button @click="logout" class="text-sm text-gray-400 hover:text-cyber-pink transition-colors">Log Out [x]</button>
    </div>

    <div v-if="error" class="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-md mb-6 font-mono">
      > ERROR: {{ error }}
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      
      <!-- Target Selection -->
      <div class="space-y-6">
        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">Guild ID (Server)</label>
          <div class="flex gap-2">
            <input v-model="guildId" type="text" class="neon-input flex-1" placeholder="Es. 1529123644842705018">
            <button @click="loadConfig" :disabled="isLoading" class="bg-gray-800 hover:bg-gray-700 px-4 rounded border border-gray-600 transition-colors">
              SCAN
            </button>
          </div>
        </div>

        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">Source Channel ID</label>
          <select v-model="sourceChannelId" class="neon-input bg-gray-900">
            <option value="">Seleziona Canale</option>
            <option v-for="ch in availableChannels" :key="ch.id" :value="ch.id">
              {{ ch.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">Authorized Role ID (Opzionale)</label>
          <select v-model="sourceRoleId" class="neon-input bg-gray-900 border-cyber-purple/50 focus:border-cyber-purple">
            <option value="">Lascia vuoto per tutti</option>
            <option v-for="r in availableRoles" :key="r.id" :value="r.id">
              {{ r.name }}
            </option>
          </select>
          <p class="text-xs text-gray-500 mt-1 font-mono">Se impostato, il bot ascolterà solo chi ha questo ruolo.</p>
        </div>
      </div>

      <!-- Destinations -->
      <div class="space-y-6">
        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">Destination Channels (ID)</label>
          <div class="h-48 overflow-y-auto border border-gray-800 rounded bg-gray-900/50 p-2 space-y-2 custom-scrollbar">
            <label v-for="ch in availableChannels" :key="ch.id" class="flex items-center gap-2 p-2 hover:bg-gray-800 rounded cursor-pointer">
              <input type="checkbox" :value="ch.id" v-model="destChannels" class="accent-cyber-cyan w-4 h-4">
              <span class="text-gray-300 font-mono text-sm">{{ ch.name }}</span>
            </label>
            <div v-if="availableChannels.length === 0" class="text-gray-500 text-sm text-center py-10">
              Esegui SCAN per caricare i canali
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-1 font-mono">I canali in cui i cloni trasmetteranno l'audio.</p>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <input v-model="isActive" type="checkbox" id="isActive" class="w-5 h-5 accent-cyber-cyan bg-gray-900 border-gray-700 rounded">
          <label for="isActive" class="font-rajdhani text-lg text-gray-300">Abilita Broadcasting su questo Server</label>
        </div>
      </div>

    </div>

    <div class="mt-10 pt-6 border-t border-gray-800 flex justify-end">
      <button @click="saveConfig" :disabled="isLoading" class="neon-btn-primary w-full md:w-auto px-12">
        {{ isLoading ? 'UPLOADING...' : 'SAVE TO MAINFRAME' }}
      </button>
    </div>
    
    <!-- Terminal / Logs Section -->
    <div class="mt-8 border border-gray-800 rounded bg-black/60 overflow-hidden">
      <div 
        class="bg-gray-900/80 p-3 flex justify-between items-center transition-colors"
      >
        <div @click="toggleLogs" class="font-rajdhani text-cyber-cyan font-bold flex items-center gap-2 cursor-pointer hover:text-white">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
          BOT LOGS TERMINAL
          <span class="text-gray-500 font-mono text-sm">[{{ showLogs ? '-' : '+' }}]</span>
        </div>
        <button @click="restartSystem" :disabled="isLoading" class="text-xs bg-red-900/40 hover:bg-red-800 text-red-200 border border-red-700/50 px-3 py-1 rounded transition-colors flex items-center gap-1 disabled:opacity-50">
           <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
           RESTART SYSTEM
        </button>
      </div>
      <div v-if="showLogs" class="p-4 h-64 overflow-y-auto font-mono text-sm text-gray-300 space-y-1 custom-scrollbar">
        <div v-for="(log, idx) in logs" :key="idx" class="border-b border-gray-800/50 pb-1">
          <span class="text-gray-500">[{{ new Date(log.timestamp).toLocaleTimeString() }}]</span>
          <span :class="log.level === 'error' ? 'text-red-400' : 'text-cyber-green ml-2'">{{ log.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="text-gray-600 italic">Nessun log disponibile...</div>
      </div>
    </div>
  </div>
</template>
