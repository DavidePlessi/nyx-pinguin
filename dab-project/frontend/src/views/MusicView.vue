<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CyberModal from '../components/CyberModal.vue'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()
const route = useRoute()

const guildId = ref((route.query.guild || route.query.id || '') as string)
const availableChannels = ref<any[]>([])
const selectedChannelId = ref('')
const searchQuery = ref('')
const botQueries = ref<Record<string, string>>({})
const isLoading = ref(false)
const error = ref('')

const musicStatus = ref<any>({ active_bots: [] })
let pollInterval: any = null
const loadingBots = ref<Set<string>>(new Set())

const modalState = ref({
  show: false,
  title: 'SYSTEM ALERT',
  message: '',
  isConfirm: false,
  resolve: null as ((value: boolean) => void) | null
})

const handleModalConfirm = () => {
  if (modalState.value.resolve) modalState.value.resolve(true)
  modalState.value.show = false
}

const handleModalCancel = () => {
  if (modalState.value.resolve) modalState.value.resolve(false)
  modalState.value.show = false
}

const fetchChannels = async () => {
  if (!guildId.value) return
  try {
    const res = await fetch(`${BACKEND_URL}/api/discord/guilds/${guildId.value}/channels`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) availableChannels.value = await res.json()
  } catch (e) {
    console.error("Failed to fetch channels", e)
  }
}

const loadMusicStatus = async () => {
  if (!guildId.value) return
  
  if (route.query.guild !== guildId.value && route.query.id !== guildId.value) {
    router.replace({ query: { ...route.query, guild: guildId.value } })
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/music/status/${guildId.value}`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.status === 401 || res.status === 403) {
       localStorage.removeItem('dab_session_token')
       router.replace({ name: 'Login', query: { guild: guildId.value } })
       return
    }
    if (res.ok) {
      musicStatus.value = await res.json()
      loadingBots.value.clear() // Clear loading state once data is refreshed
    }
  } catch (err) {
    console.error("Failed to load music status", err)
    loadingBots.value.clear()
  }
}

const sendCommand = async (action: string, bot_id?: string, query?: string) => {
  if (!guildId.value) {
    error.value = t('music.errorGuild') || 'Guild ID required'
    return
  }

  if ((action === 'play' || action === 'insert') && !selectedChannelId.value && !bot_id) {
    error.value = t('music.errorChannel') || 'Select a voice channel first'
    return
  }

  if ((action === 'play' || action === 'insert') && !query) {
    error.value = t('music.errorQuery') || 'Query cannot be empty'
    return
  }

  isLoading.value = true
  if (bot_id) loadingBots.value.add(bot_id)
  error.value = ''

  try {
    const res = await fetch(`${BACKEND_URL}/api/music/command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionToken.value}`
      },
      body: JSON.stringify({
        guild_id: guildId.value,
        action,
        query,
        voice_channel_id: selectedChannelId.value,
        bot_id
      })
    })
    
    if (!res.ok) throw new Error("Failed to send command")
    
    if (action === 'play' || action === 'insert') {
       searchQuery.value = '' 
    }
    
    setTimeout(loadMusicStatus, 1000)
    
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const getChannelName = (id: string) => {
  const ch = availableChannels.value.find(c => c.id === id)
  return ch ? ch.name : id
}

const formatDuration = (ms: number | string) => {
  if (typeof ms === 'string') return ms
  if (!ms) return '0:00'
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

onMounted(() => {
  if (guildId.value && sessionToken.value) {
    fetchChannels()
    loadMusicStatus()
    pollInterval = setInterval(loadMusicStatus, 1500)
  }
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

const onGuildScan = () => {
    fetchChannels()
    loadMusicStatus()
    if (!pollInterval) {
        pollInterval = setInterval(loadMusicStatus, 1500)
    }
}
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
    
    <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-8 border-b border-gray-800 pb-4">
      <h2 class="font-rajdhani text-2xl md:text-3xl font-bold neon-text-purple text-center md:text-left">{{ t('music.title') || 'MUSIC PLAYER' }}</h2>
      <div class="flex items-center gap-4">
        <router-link to="/" class="text-sm text-cyber-cyan hover:text-white transition-colors whitespace-nowrap font-bold flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
          BACK TO HUB
        </router-link>
      </div>
    </div>

    <div v-if="error" class="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-md mb-6 font-mono">
      > ERROR: {{ error }}
    </div>

    <div class="grid grid-cols-1 md:grid-cols-12 gap-4 mb-8">
      <div class="md:col-span-3">
        <div class="flex gap-2">
            <input v-model="guildId" type="text" class="neon-input flex-1" :placeholder="t('music.guildIdLabel') || 'Guild ID'">
            <button @click="onGuildScan" class="bg-gray-800 hover:bg-gray-700 px-3 rounded border border-gray-600 transition-colors">
              {{ t('music.scan') || 'SCAN' }}
            </button>
        </div>
      </div>
      <div class="md:col-span-3">
        <select v-model="selectedChannelId" class="neon-input bg-gray-900 w-full border-cyber-purple/50 focus:border-cyber-purple">
          <option value="">{{ t('music.selectChannel') || 'Select Channel' }}</option>
          <option v-for="ch in availableChannels" :key="ch.id" :value="ch.id">
            {{ ch.name }}
          </option>
        </select>
      </div>
      <div class="md:col-span-6 flex gap-2">
        <input v-model="searchQuery" type="text" class="neon-input flex-1 border-cyber-purple/50 focus:border-cyber-purple text-lg" :placeholder="t('music.urlPlaceholder') || 'Search or Link...'" @keyup.enter="sendCommand('play', undefined, searchQuery)">
        <button @click="sendCommand('play', undefined, searchQuery)" :disabled="isLoading" class="bg-cyber-purple/20 text-cyber-purple border border-cyber-purple hover:bg-cyber-purple hover:text-white px-6 rounded font-bold transition-all shadow-[0_0_10px_rgba(188,19,254,0.3)] hover:shadow-[0_0_20px_rgba(188,19,254,0.6)] flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
          <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          {{ isLoading ? 'LOADING...' : (t('music.play') || 'PLAY') }}
        </button>
        <button @click="sendCommand('insert', undefined, searchQuery)" :disabled="isLoading" class="bg-gray-800 text-gray-300 border border-gray-600 hover:bg-gray-700 hover:text-white px-4 rounded font-bold transition-all flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed">
          <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          {{ isLoading ? '...' : (t('music.insert') || 'INSERT') }}
        </button>
      </div>
    </div>

    <div v-if="musicStatus?.active_bots?.length > 0" class="flex flex-col gap-6 w-full">
      <div v-for="bot in musicStatus.active_bots" :key="bot.bot_id" class="bg-gray-900/60 border border-gray-700 rounded-lg shadow-[0_0_15px_rgba(0,0,0,0.5)] flex flex-col lg:flex-row relative overflow-hidden group">
        
        <!-- Loading Overlay -->
        <div v-if="loadingBots.has(bot.bot_id)" class="absolute inset-0 bg-black/70 z-50 flex items-center justify-center backdrop-blur-sm transition-opacity">
           <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyber-cyan"></div>
        </div>

        <div v-if="bot.current_track?.thumbnail" class="absolute inset-0 opacity-10 bg-cover bg-center blur-md z-0 pointer-events-none" :style="`background-image: url('${bot.current_track.thumbnail}')`"></div>

        <!-- Left Side: Now Playing (Player) -->
        <div class="relative z-10 w-full lg:w-[400px] xl:w-[450px] shrink-0 p-6 flex flex-col">
          <div class="flex justify-between items-center mb-6 border-b border-gray-800 pb-3">
             <div class="flex items-center gap-3">
                <span class="text-xs bg-cyber-purple/20 text-cyber-purple border border-cyber-purple/50 px-2 py-1 rounded font-mono shadow-[0_0_5px_rgba(188,19,254,0.3)]">Bot: {{ bot.bot_id }}</span>
                <span class="text-sm text-gray-400 font-mono flex items-center gap-1">
                  <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z"></path></svg>
                  {{ getChannelName(bot.channel_id) }}
                </span>
             </div>
             <button @click="sendCommand('stop', bot.bot_id)" class="text-red-500 hover:text-red-400 p-2 bg-red-900/30 rounded border border-red-900/50 hover:bg-red-900/50 transition-colors shadow-[0_0_5px_rgba(239,68,68,0.2)] hover:shadow-[0_0_10px_rgba(239,68,68,0.5)]" title="Stop">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path></svg>
             </button>
          </div>

          <div v-if="bot.current_track" class="flex flex-col items-center text-center gap-6 mb-4 flex-1">
            <img v-if="bot.current_track.thumbnail" :src="bot.current_track.thumbnail" class="w-48 h-48 sm:w-56 sm:h-56 rounded-2xl object-cover shadow-[0_0_25px_rgba(0,0,0,0.8)] border border-gray-700/50 shrink-0" />
            <div class="w-full">
              <h3 class="text-white font-bold text-2xl sm:text-3xl truncate mb-2" :title="bot.current_track.title">{{ bot.current_track.title }}</h3>
              <p class="text-cyber-cyan text-base font-mono mb-6">
                 {{ formatDuration(bot.current_track.duration) }} 
                 <span v-if="bot.is_paused" class="ml-2 text-yellow-500">[PAUSED]</span>
              </p>
              
              <!-- Controls -->
              <div class="flex justify-center items-center gap-6 mt-4">
                <button @click="sendCommand('previous', bot.bot_id)" class="text-gray-400 hover:text-white transition transform hover:scale-110 p-2">
                  <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20"><path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 14V6a1 1 0 00-1.555-.832L10 8.798V6a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z"></path></svg>
                </button>
                <button v-if="bot.is_paused" @click="sendCommand('resume', bot.bot_id)" class="text-cyber-cyan hover:text-white transition transform hover:scale-110 p-2">
                  <svg class="w-12 h-12 drop-shadow-[0_0_10px_rgba(0,255,255,0.6)]" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>
                </button>
                <button v-else @click="sendCommand('pause', bot.bot_id)" class="text-cyber-purple hover:text-white transition transform hover:scale-110 p-2">
                  <svg class="w-12 h-12 drop-shadow-[0_0_10px_rgba(188,19,254,0.6)]" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>
                </button>
                <button @click="sendCommand('skip', bot.bot_id)" class="text-gray-400 hover:text-white transition transform hover:scale-110 p-2">
                  <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20"><path d="M4.555 5.168A1 1 0 003 6v8a1 1 0 001.555.832L10 11.202V14a1 1 0 001.555.832l6-4a1 1 0 000-1.664l-6-4A1 1 0 0010 6v2.798L4.555 5.168z"></path></svg>
                </button>
              </div>
              
              <!-- Add to Queue (Bot Specific) -->
              <div class="mt-6 flex gap-2 w-full max-w-sm mx-auto">
                 <input v-model="botQueries[bot.bot_id]" type="text" class="neon-input flex-1 text-sm py-1.5 px-3 bg-black/40 border-gray-700 focus:border-cyber-purple" placeholder="Link o brano..." @keyup.enter="sendCommand('play', bot.bot_id, botQueries[bot.bot_id]); botQueries[bot.bot_id] = ''">
                 <button @click="sendCommand('play', bot.bot_id, botQueries[bot.bot_id]); botQueries[bot.bot_id] = ''" :disabled="isLoading || !botQueries[bot.bot_id]" class="bg-cyber-purple/20 text-cyber-purple border border-cyber-purple hover:bg-cyber-purple hover:text-white px-3 py-1 rounded text-xs font-bold transition-all disabled:opacity-50">
                   PLAY
                 </button>
                 <button @click="sendCommand('insert', bot.bot_id, botQueries[bot.bot_id]); botQueries[bot.bot_id] = ''" :disabled="isLoading || !botQueries[bot.bot_id]" class="bg-gray-800 text-gray-300 border border-gray-600 hover:bg-gray-700 hover:text-white px-3 py-1 rounded text-xs font-bold transition-all disabled:opacity-50">
                   INSERT
                 </button>
              </div>

            </div>
          </div>
          <div v-else class="flex-1 flex items-center justify-center text-gray-500 italic mb-6">
             {{ t('music.emptyQueue') }}
          </div>
        </div>

        <!-- Right Side: Queue -->
        <div class="relative z-10 flex-1 p-6 lg:border-l lg:border-gray-800 bg-black/20 flex flex-col min-w-0">
          <h4 class="text-sm font-rajdhani text-gray-400 uppercase tracking-widest mb-4 flex items-center justify-between border-b border-gray-800/50 pb-2 shrink-0">
            {{ t('music.queue') || 'QUEUE' }}
            <span class="text-cyber-cyan bg-cyber-cyan/10 px-2 py-0.5 rounded">{{ bot.queue?.length || 0 }}</span>
          </h4>
          <div class="space-y-3 overflow-y-auto custom-scrollbar pr-2 h-72 lg:h-[450px]">
             <div v-for="(t, i) in bot.queue" :key="i" class="flex items-center gap-4 bg-gray-800/40 border border-gray-700/50 p-3 rounded hover:bg-gray-700 transition">
                <div class="text-xs text-gray-500 w-4 text-center font-mono">{{ Number(i) + 1 }}</div>
                <img v-if="t.thumbnail" :src="t.thumbnail" class="w-12 h-12 rounded object-cover shadow-sm shrink-0" />
                <div class="text-base text-gray-200 truncate flex-1 font-medium" :title="t.title">{{ t.title }}</div>
             </div>
             <div v-if="!bot.queue || bot.queue.length === 0" class="text-sm text-gray-500 italic py-8 text-center h-full flex items-center justify-center">
               {{ t('music.emptyQueue') || 'Empty' }}
             </div>
          </div>
        </div>

      </div>
    </div>
    
    <div v-else class="text-center py-20 text-gray-500 border border-dashed border-gray-700 rounded-lg bg-gray-900/30">
      <svg class="w-16 h-16 mx-auto mb-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
      <p class="font-rajdhani text-xl">{{ t('music.noBots') || 'No active bots.' }}</p>
    </div>

  </div>
</template>
