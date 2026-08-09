<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
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

const checkAuthUrl = () => {
  const urlParams = new URLSearchParams(window.location.search)
  const token = urlParams.get('token')
  if (token) {
    localStorage.setItem('dab_session_token', token)
    sessionToken.value = token
    window.history.replaceState({}, document.title, window.location.pathname)
  }
}

const loginWithDiscord = () => {
  window.location.href = `${BACKEND_URL}/api/oauth/login`
}

const logout = () => {
  localStorage.removeItem('dab_session_token')
  sessionToken.value = null
  if (logsInterval) clearInterval(logsInterval)
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
    alert("✅ Configurazione salvata nel mainframe!")
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  checkAuthUrl()
})
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
    </header>

    <!-- Not Authenticated -->
    <div v-if="!sessionToken" class="flex flex-col items-center justify-center h-64">
      <div class="glass-panel p-10 text-center max-w-md w-full">
        <h2 class="font-orbitron text-2xl mb-6 text-gray-300">ADMIN ACCESS REQUIRED</h2>
        <button @click="loginWithDiscord" class="neon-btn-primary w-full flex items-center justify-center gap-3">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"/></svg>
          AUTHENTICATE
        </button>
      </div>
    </div>

    <!-- Authenticated Dashboard -->
    <div v-else class="glass-panel p-8">
      
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
          @click="toggleLogs"
          class="bg-gray-900/80 p-3 flex justify-between items-center cursor-pointer hover:bg-gray-800 transition-colors"
        >
          <div class="font-rajdhani text-cyber-cyan font-bold flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
            BOT LOGS TERMINAL
          </div>
          <span class="text-gray-500 font-mono text-sm">[{{ showLogs ? '-' : '+' }}]</span>
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
  </div>
</template>
