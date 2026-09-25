<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()

const isLoading = ref(false)
const error = ref('')

const userGuilds = ref<string[]>([])
const userGuildsInfo = ref<any[]>([])
const selectedGuild = ref<string>('')

const activePolls = ref<any[]>([])
const dropHistory = ref<any[]>([])

const fetchPublicData = async () => {
  if (!selectedGuild.value) return
  isLoading.value = true
  try {
    const [pollsRes, historyRes] = await Promise.all([
      fetch(`${BACKEND_URL}/api/drops/guilds/${selectedGuild.value}/public_polls`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } }),
      fetch(`${BACKEND_URL}/api/drops/guilds/${selectedGuild.value}/history`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } })
    ])
    
    if (pollsRes.ok) {
      activePolls.value = await pollsRes.json()
    }
    
    if (historyRes.ok) {
      dropHistory.value = await historyRes.json()
    }
  } catch (e) {
    console.error(e)
    error.value = 'Errore nel caricamento dei dati.'
  } finally {
    isLoading.value = false
  }
}

const onGuildChange = () => {
  fetchPublicData()
}

const initUser = async () => {
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/me`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } })
    if (res.ok) {
      const data = await res.json()
      userGuilds.value = data.guilds || []
      userGuildsInfo.value = data.guilds_info || []
      
      if (userGuilds.value.length > 0) {
        selectedGuild.value = userGuilds.value[0]
        onGuildChange()
      }
    }
  } catch(e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const formatDate = (ds: string) => {
  if (!ds) return ''
  const d = new Date(ds)
  return d.toLocaleString()
}

onMounted(() => {
  if (!sessionToken.value) {
    router.replace({ name: 'Login' })
    return
  }
  initUser()
})
</script>

<template>
  <div class="p-4 md:p-8 max-w-7xl mx-auto animate-fade-in">
    <div class="flex flex-col sm:flex-row justify-between items-center mb-8 border-b border-gray-800 pb-4 gap-4 text-center sm:text-left">
      <h2 class="font-rajdhani text-3xl font-bold text-cyber-purple tracking-wider uppercase">{{ t('dashboard.publicDrops') }}</h2>
      <button @click="$router.push('/')" class="text-sm text-gray-500 hover:text-cyber-cyan transition-colors font-mono">
        {{ t('app.backToHub') }}
      </button>
    </div>
    
    <div v-if="userGuilds.length === 0 && !isLoading" class="glass-panel p-6 rounded-xl text-center">
      <p class="text-gray-400 font-mono">{{ t('drops.noAuthorizedGuild') }}</p>
    </div>
    
    <div v-else>
      <div v-if="userGuilds.length > 1" class="bg-gray-900/50 border border-gray-800 p-6 rounded mb-6 flex flex-col md:flex-row gap-4 md:items-center">
        <label class="font-rajdhani text-gray-400 uppercase tracking-wide">{{ t('drops.selectGuildToManage') }}</label>
        <select v-model="selectedGuild" @change="onGuildChange" class="neon-input bg-gray-900 w-full md:w-1/3">
          <option v-for="g in userGuildsInfo" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
      </div>
      
      <div v-if="userGuilds.length === 1" class="bg-gray-900/50 border border-gray-800 p-6 rounded mb-6 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full border border-gray-700 overflow-hidden flex items-center justify-center bg-gray-800">
          <img v-if="userGuildsInfo[0]?.icon" :src="`https://cdn.discordapp.com/icons/${selectedGuild}/${userGuildsInfo[0].icon}.png`" class="w-full h-full object-cover">
          <span v-else class="text-gray-400 font-bold">{{ userGuildsInfo[0]?.name?.charAt(0) || 'G' }}</span>
        </div>
        <div>
          <h3 class="font-rajdhani text-xl text-gray-200 font-bold uppercase">{{ userGuildsInfo[0]?.name }}</h3>
        </div>
      </div>
      
      <div v-if="selectedGuild">
        <div class="flex justify-end mb-4">
          <button @click="fetchPublicData" class="px-4 py-2 bg-gray-900/50 hover:bg-gray-800 text-cyber-cyan font-orbitron text-sm rounded border border-cyber-cyan/30 transition-colors flex items-center gap-2 shadow-[0_0_10px_rgba(0,255,255,0.1)]">
            <svg class="w-4 h-4" :class="{'animate-spin': isLoading}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            {{ t('drops.refreshData') }}
          </button>
        </div>

        <!-- ACTIVE POLLS -->
        <div class="bg-gray-900/50 border border-gray-800 rounded p-6 mb-6">
          <h3 class="font-rajdhani text-xl text-cyber-purple mb-4 font-bold flex items-center gap-2">
            {{ t('drops.activePolls') }}
          </h3>
          <div v-if="isLoading && activePolls.length === 0" class="text-gray-500 font-mono animate-pulse">{{ t('drops.loadingDrops') }}</div>
          <div v-else-if="activePolls.length === 0" class="text-gray-500 italic text-sm">{{ t('drops.noActivePolls') }}</div>
          <div v-else class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            <div v-for="poll in activePolls" :key="poll.id" class="border border-cyber-purple/30 bg-gray-800/30 p-4 rounded flex flex-col justify-between">
              <div>
                <h4 class="text-cyber-cyan font-bold font-rajdhani text-lg mb-2 flex justify-between">
                  {{ poll.item_name }}
                  <span v-if="poll.poll_type === 'lucent'" class="text-yellow-400 text-sm">{{ t('drops.total') }} {{ poll.amount }}</span>
                </h4>
                <div class="mb-4">
                  <p class="text-xs text-gray-400 mb-2 uppercase tracking-wide border-b border-gray-700 pb-1 flex justify-between">
                    {{ t('drops.candidates') }} <span class="text-cyber-cyan">{{ poll.candidates_info.length }}</span>
                  </p>
                  <div class="max-h-32 overflow-y-auto custom-scrollbar pr-2">
                    <div v-for="c in poll.candidates_info" :key="c.discord_id" class="flex justify-between items-center text-sm py-1 border-b border-gray-800/50 last:border-0">
                      <span class="text-gray-300">{{ c.username }}</span>
                      <div class="flex items-center gap-2">
                        <span v-if="poll.poll_type === 'lucent'" class="text-yellow-500 font-mono text-xs">{{ c.amount }}</span>
                        <span class="text-xs text-gray-500 truncate max-w-[100px]" :title="c.reason">{{ c.reason }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- HISTORY -->
        <div class="bg-gray-900/50 border border-gray-800 rounded p-6">
          <h3 class="font-rajdhani text-xl text-cyber-purple mb-4 font-bold flex items-center gap-2">
            {{ t('drops.historyTitle') }}
          </h3>
          <div v-if="isLoading && dropHistory.length === 0" class="text-gray-500 font-mono animate-pulse">{{ t('drops.loadingDrops') }}</div>
          <div v-else-if="dropHistory.length === 0" class="text-gray-500 italic text-sm">{{ t('drops.noAssignmentHistory') }}</div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-gray-800 text-gray-400 font-rajdhani uppercase tracking-wide text-sm">
                  <th class="py-3 px-4">{{ t('drops.date') }}</th>
                  <th class="py-3 px-4">{{ t('drops.item') }}</th>
                  <th class="py-3 px-4">{{ t('drops.assignedTo') }}</th>
                  <th class="py-3 px-4">{{ t('drops.reason') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="h in dropHistory" :key="h.id" class="border-b border-gray-800/50 hover:bg-gray-800/20 transition-colors">
                  <td class="py-3 px-4 text-sm text-gray-500 font-mono">{{ formatDate(h.assigned_at) }}</td>
                  <td class="py-3 px-4">
                    <span class="text-cyber-cyan font-bold" :class="{'text-yellow-400': h.poll_type === 'lucent'}">
                      {{ h.item_name }} <span v-if="h.amount">({{ h.amount }})</span>
                    </span>
                  </td>
                  <td class="py-3 px-4 text-gray-300 font-mono text-sm">{{ h.username }}</td>
                  <td class="py-3 px-4 text-gray-500 text-sm">{{ h.reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
      </div>
    </div>
  </div>
</template>
