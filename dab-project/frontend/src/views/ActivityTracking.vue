<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { t } from '../i18n'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend)

import CyberModal from '../components/CyberModal.vue'

const modalState = ref({
  show: false,
  title: '',
  message: '',
  isConfirm: false,
  resolve: null as ((value: boolean) => void) | null
})

const showAlert = (message: string, title?: string) => {
  return new Promise<boolean>((resolve) => {
    modalState.value = { show: true, title: title || t('modal.systemAlert'), message, isConfirm: false, resolve }
  })
}

const showConfirm = (message: string, title?: string) => {
  return new Promise<boolean>((resolve) => {
    modalState.value = { show: true, title: title || t('modal.systemAlert'), message, isConfirm: true, resolve }
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

const activities = ref<any[]>([])
const eventsList = ref<any[]>([])
const weeklyData = ref<Record<string, any>>({})
const totalEvents = ref(0)
const dropConfig = ref({ min_events: 2, min_weekly_activity: 5500 })

const activeTab = ref('player') // 'player' or 'event'
const expandedEvents = ref<Set<string>>(new Set())
const expandedPlayers = ref<Set<string>>(new Set())
const playerSearchQuery = ref('')
const isChartExpanded = ref(false)

const loading = ref(true)
const syncing = ref(false)

const sortKey = ref('total_events')
const sortDesc = ref(true)

const fromDate = ref('')
const toDate = ref('')

const selectedPlayers = ref<Set<string>>(new Set())

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const userRole = ref<string>('user')
const adminGuilds = ref<string[]>([])
const adminGuildsInfo = ref<any[]>([])
const adminGuildId = ref<string>('')
const targetWeekId = ref('')

// Chart color palette
const colors = [
  '#4ade80', '#60a5fa', '#f472b6', '#fbbf24', '#a78bfa',
  '#2dd4bf', '#fb923c', '#f87171', '#38bdf8', '#c0caf5'
]

const availableWeeks = computed(() => {
  return Object.keys(weeklyData.value).sort().reverse()
})

const fetchActivity = async () => {
  if (!adminGuildId.value) return
  loading.value = true
  try {
    let url = `${BACKEND_URL}/api/activity/${adminGuildId.value}?`
    if (fromDate.value) url += `from_date=${new Date(fromDate.value).toISOString()}&`
    if (toDate.value) {
      let tDate = new Date(toDate.value)
      tDate.setHours(23, 59, 59, 999)
      url += `to_date=${tDate.toISOString()}&`
    }
    if (targetWeekId.value) {
      url += `target_week_id=${targetWeekId.value}&`
    }
    
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    const data = await res.json()
    if (data.players) {
      activities.value = data.players
      eventsList.value = data.events || []
      weeklyData.value = data.weekly_data || {}
      totalEvents.value = data.total_events || 0
      if (data.drop_config) {
        dropConfig.value = data.drop_config
      }
      
      // Auto-select top 10 players for chart if none selected
      if (selectedPlayers.value.size === 0 && activities.value.length > 0) {
        const top10 = [...activities.value].sort((a, b) => b.total_events - a.total_events).slice(0, 10)
        top10.forEach(p => selectedPlayers.value.add(p.player_id))
      }
    } else {
      activities.value = []
      eventsList.value = []
      weeklyData.value = {}
      totalEvents.value = 0
    }
  } catch (err) {
    console.error('Failed to fetch activity', err)
  } finally {
    loading.value = false
  }
}

const forceSync = async () => {
  if (!adminGuildId.value) return
  syncing.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/activity/sync/${adminGuildId.value}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      await fetchActivity()
    } else {
      const data = await res.json()
      await showAlert('Sync failed: ' + (data.detail || 'Unknown error'), 'ERRORE')
    }
  } catch (err) {
    console.error('Failed to sync', err)
    await showAlert('Network error', 'ERRORE')
  } finally {
    syncing.value = false
  }
}

const triggerLogMessage = async () => {
  if (!adminGuildId.value) return
  
  const confirmed = await showConfirm("Sei sicuro di voler inviare il messaggio di log attività su Discord ora?", "CONFERMA")
  if (!confirmed) return
  
  syncing.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/activity/trigger_log_message/${adminGuildId.value}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      await showAlert('Messaggio inviato con successo!', 'SUCCESSO')
    } else {
      const data = await res.json()
      await showAlert('Errore: ' + (data.detail || 'Errore sconosciuto'), 'ERRORE')
    }
  } catch (err) {
    console.error('Failed to trigger message', err)
    await showAlert('Errore di rete', 'ERRORE')
  } finally {
    syncing.value = false
  }
}

const initActivityAdmin = async () => {
  loading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/me`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } })
    if (res.ok) {
      const data = await res.json()
      adminGuilds.value = data.guilds || []
      adminGuildsInfo.value = data.guilds_info || []
      
      if (adminGuilds.value.length > 0) {
        adminGuildId.value = adminGuilds.value[0]
        // Default to last 30 days
        const thirtyDaysAgo = new Date()
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
        fromDate.value = thirtyDaysAgo.toISOString().split('T')[0]
        
        fetchActivity()
      } else {
        loading.value = false
      }
    } else {
      loading.value = false
    }
  } catch(e) {
    console.error(e)
    loading.value = false
  }
}

const onGuildChange = () => {
  selectedPlayers.value.clear()
  fetchActivity()
}

onMounted(() => {
  if (sessionToken.value) {
    try {
      const base64Url = sessionToken.value.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join('')))
      if (payload) {
        userRole.value = payload.role || 'user'
      }
    } catch (e) {
      console.error('Invalid token', e)
    }
  }
  initActivityAdmin()
})

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortDesc.value = !sortDesc.value
  } else {
    sortKey.value = key
    sortDesc.value = true
  }
}

const togglePlayerExpansion = (playerId: string) => {
  if (expandedPlayers.value.has(playerId)) {
    expandedPlayers.value.delete(playerId)
  } else {
    expandedPlayers.value.add(playerId)
  }
}

const toggleEvent = (eventId: string) => {
  if (expandedEvents.value.has(eventId)) {
    expandedEvents.value.delete(eventId)
  } else {
    expandedEvents.value.add(eventId)
  }
}

const sortedActivities = computed(() => {
  let filtered = activities.value
  
  if (playerSearchQuery.value) {
    const q = playerSearchQuery.value.toLowerCase()
    filtered = filtered.filter(p => p.player_name.toLowerCase().includes(q))
  }
  
  return [...filtered].sort((a, b) => {
    let valA = a[sortKey.value]
    let valB = b[sortKey.value]
    
    // Add computed attendance field for sorting
    if (sortKey.value === 'attendance') {
        valA = totalEvents.value ? (a.total_events / totalEvents.value) : 0
        valB = totalEvents.value ? (b.total_events / totalEvents.value) : 0
    }

    if (typeof valA === 'string') valA = valA.toLowerCase()
    if (typeof valB === 'string') valB = valB.toLowerCase()

    if (valA < valB) return sortDesc.value ? 1 : -1
    if (valA > valB) return sortDesc.value ? -1 : 1
    return 0
  })
})

const togglePlayerSelection = (playerId: string) => {
  if (selectedPlayers.value.has(playerId)) {
    selectedPlayers.value.delete(playerId)
  } else {
    selectedPlayers.value.add(playerId)
  }
}

const sortedEventsList = computed(() => {
  return [...eventsList.value].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
})

const chartData = computed(() => {
  const weeks = Object.keys(weeklyData.value).sort()
  const datasets: any[] = []
  
  let colorIndex = 0
  
  selectedPlayers.value.forEach(playerId => {
    const playerObj = activities.value.find(p => p.player_id === playerId)
    if (!playerObj) return
    
    const dataPoints = weeks.map(w => {
      return weeklyData.value[w][playerId] || 0
    })
    
    datasets.push({
      label: playerObj.player_name,
      borderColor: colors[colorIndex % colors.length],
      backgroundColor: colors[colorIndex % colors.length],
      data: dataPoints,
      tension: 0.3
    })
    colorIndex++
  })
  
  return {
    labels: weeks,
    datasets
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#d1d5db' // gray-300
      }
    }
  },
  scales: {
    y: {
      ticks: { color: '#9ca3af', stepSize: 1 },
      grid: { color: '#374151' } // gray-700
    },
    x: {
      ticks: { color: '#9ca3af' },
      grid: { color: '#374151' }
    }
  }
}

// Watch filters to trigger fetch
watch([fromDate, toDate], () => {
  fetchActivity()
})
</script>

<template>
  <div class="p-4 sm:p-6 max-w-7xl mx-auto">
    <CyberModal 
      :show="modalState.show" 
      :title="modalState.title" 
      :message="modalState.message" 
      :isConfirm="modalState.isConfirm"
      @confirm="handleModalConfirm"
      @cancel="handleModalCancel"
    />
    
    <div class="flex flex-col xl:flex-row justify-between items-start xl:items-center mb-6 gap-4">
      <h1 class="text-2xl sm:text-3xl font-bold text-gray-100 uppercase tracking-wide w-full xl:w-auto text-center xl:text-left">{{ t('activity.title') }}</h1>
      
      <div class="flex flex-col sm:flex-row flex-wrap items-center gap-3 sm:gap-4 w-full xl:w-auto justify-center xl:justify-end">
        <!-- Date Filters -->
        <div class="flex items-center gap-2 w-full sm:w-auto justify-center">
          <input type="date" v-model="fromDate" class="bg-gray-800 border border-gray-700 text-gray-300 px-3 py-2 sm:py-1 rounded outline-none focus:border-blue-500 text-sm flex-1 sm:flex-none">
          <span class="text-gray-500 px-1">{{ t('activity.to') }}</span>
          <input type="date" v-model="toDate" class="bg-gray-800 border border-gray-700 text-gray-300 px-3 py-2 sm:py-1 rounded outline-none focus:border-blue-500 text-sm flex-1 sm:flex-none">
        </div>

        <select 
          v-if="adminGuildsInfo.length > 0" 
          v-model="adminGuildId" 
          @change="onGuildChange"
          class="bg-gray-800 border border-gray-700 text-gray-200 px-3 py-2 sm:py-1 rounded outline-none focus:border-blue-500 font-bold w-full sm:w-auto max-w-xs"
        >
          <option v-for="g in adminGuildsInfo" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
        
        <button 
          v-if="['admin', 'guild_admin'].includes(userRole)"
          @click="forceSync" 
          :disabled="syncing || !adminGuildId"
          title="Force Sync Raid-Helper"
          class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded font-medium disabled:opacity-50 flex items-center justify-center gap-2 w-full sm:w-auto"
        >
          <svg class="w-4 h-4" :class="{'animate-spin': syncing}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
        </button>
        
        <button 
          v-if="['admin', 'guild_admin'].includes(userRole)"
          @click="triggerLogMessage" 
          :disabled="syncing || !adminGuildId"
          title="Invia messaggio settimanale ora"
          class="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded font-medium disabled:opacity-50 flex items-center justify-center gap-2 w-full sm:w-auto"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
        </button>
      </div>
    </div>
    
    <div v-if="loading" class="text-center py-10 text-gray-400 font-mono animate-pulse">{{ t('activity.loading') }}</div>
    <div v-else-if="!adminGuildId" class="text-center py-10 text-gray-500">{{ t('activity.noGuilds') }}</div>
    <div v-else class="space-y-6">
      
      <!-- Tabs -->
      <div class="flex border-b border-gray-700 overflow-x-auto whitespace-nowrap">
        <button 
          @click="activeTab = 'player'" 
          class="px-4 sm:px-6 py-3 font-semibold text-sm transition-colors border-b-2 flex-1 sm:flex-none"
          :class="activeTab === 'player' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          {{ t('activity.playerCentric') }}
        </button>
        <button 
          @click="activeTab = 'event'" 
          class="px-4 sm:px-6 py-3 font-semibold text-sm transition-colors border-b-2 flex-1 sm:flex-none"
          :class="activeTab === 'event' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          {{ t('activity.eventCentric') }}
        </button>
        <button 
          @click="activeTab = 'eligible'" 
          class="px-4 sm:px-6 py-3 font-semibold text-sm transition-colors border-b-2 flex-1 sm:flex-none"
          :class="activeTab === 'eligible' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          {{ t('activity.eligibleForDrop') }}
        </button>
      </div>

      <!-- PLAYER CENTRIC VIEW -->
      <div v-if="activeTab === 'player'" class="space-y-6 animate-fade-in">
        <!-- Chart -->
        <div class="bg-gray-800 rounded-lg shadow border border-gray-700 overflow-hidden">
          <div 
            class="p-4 sm:p-6 bg-gray-800 hover:bg-gray-750 cursor-pointer flex justify-between items-center transition-colors"
            @click="isChartExpanded = !isChartExpanded"
          >
            <h2 class="text-lg sm:text-xl font-semibold text-gray-200 flex items-center gap-2">
              <svg class="w-5 h-5 text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
              {{ t('activity.chartTitle') }}
            </h2>
            <svg class="w-5 h-5 text-gray-500 transition-transform" :class="{'rotate-180': isChartExpanded}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </div>
          
          <div v-if="isChartExpanded" class="p-4 sm:p-6 border-t border-gray-700 bg-gray-900/20">
            <div style="height: 350px;">
              <Line v-if="chartData.labels.length > 0 && selectedPlayers.size > 0" :data="chartData" :options="chartOptions" />
              <div v-else class="text-gray-500 h-full flex items-center justify-center italic text-center p-4">
                {{ chartData.labels.length === 0 ? t('activity.chartNoEvents') : t('activity.chartNoPlayers') }}
              </div>
            </div>
            <p class="text-xs text-gray-500 mt-4 text-center px-2">{{ t('activity.chartHint') }}</p>
          </div>
        </div>

        <!-- Summary & Table / Deck -->
        <div class="bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-700">
          <div class="p-4 sm:p-4 bg-gray-900/50 border-b border-gray-700 flex justify-between items-center gap-2">
            <h2 class="text-base sm:text-lg font-semibold text-gray-200">{{ t('activity.roster') }}</h2>
            <div class="text-xs sm:text-sm font-mono text-gray-400">{{ t('activity.totalEvents') }} <strong class="text-white">{{ totalEvents }}</strong></div>
          </div>
          
          <!-- Mobile Controls (Sort & Filter) -->
          <div class="md:hidden p-4 bg-gray-900/30 border-b border-gray-700 flex flex-col gap-3">
            <input type="text" v-model="playerSearchQuery" :placeholder="t('activity.searchPlayer')" class="bg-gray-800 border border-gray-700 text-gray-200 px-3 py-2 rounded outline-none focus:border-blue-500 font-normal w-full">
            <div class="flex flex-wrap gap-2 text-xs uppercase tracking-wider font-semibold">
              <button @click="sortBy('player_name')" class="px-3 py-2 rounded border flex items-center gap-1 transition-colors" :class="{'bg-gray-700 text-white border-gray-500': sortKey === 'player_name', 'bg-gray-800 text-gray-400 border-gray-700': sortKey !== 'player_name'}">
                {{ t('activity.playerName') }}
                <span v-if="sortKey === 'player_name'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
              </button>
              <button @click="sortBy('total_events')" class="px-3 py-2 rounded border flex items-center gap-1 transition-colors" :class="{'bg-gray-700 text-white border-gray-500': sortKey === 'total_events', 'bg-gray-800 text-gray-400 border-gray-700': sortKey !== 'total_events'}">
                {{ t('activity.eventsAttended') }}
                <span v-if="sortKey === 'total_events'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
              </button>
              <button @click="sortBy('attendance')" class="px-3 py-2 rounded border flex items-center gap-1 transition-colors" :class="{'bg-gray-700 text-white border-gray-500': sortKey === 'attendance', 'bg-gray-800 text-gray-400 border-gray-700': sortKey !== 'attendance'}">
                {{ t('activity.attendance') }}
                <span v-if="sortKey === 'attendance'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
              </button>
              <button @click="sortBy('weekly_game_activity')" class="px-3 py-2 rounded border flex items-center gap-1 transition-colors" :class="{'bg-gray-700 text-white border-gray-500': sortKey === 'weekly_game_activity', 'bg-gray-800 text-gray-400 border-gray-700': sortKey !== 'weekly_game_activity'}">
                {{ t('activity.weeklyActivity') }}
                <span v-if="sortKey === 'weekly_game_activity'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
              </button>
            </div>
          </div>
          
          <!-- Mobile Deck (Cards) -->
          <div class="md:hidden p-4 space-y-4">
            <template v-for="player in sortedActivities" :key="player.player_id">
              <div 
                class="bg-gray-800 border rounded-lg p-4 transition-colors"
                :class="selectedPlayers.has(player.player_id) ? 'border-blue-500/50 bg-blue-900/20' : 'border-gray-700'"
              >
                <div class="flex justify-between items-center mb-4">
                  <div class="flex items-center gap-3 cursor-pointer" @click="togglePlayerExpansion(player.player_id)">
                    <svg class="w-5 h-5 text-gray-500 transition-transform shrink-0" :class="{'rotate-180': expandedPlayers.has(player.player_id)}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    <span class="font-bold text-gray-100 text-lg truncate flex items-center gap-2">
                      {{ player.player_name }}
                      <svg v-if="!player.has_current_weekly_activity" class="w-5 h-5 text-red-500" title="Missing Weekly Activity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                    </span>
                  </div>
                  <div class="cursor-pointer p-2 -mr-2 shrink-0" @click="togglePlayerSelection(player.player_id)">
                    <input type="checkbox" :checked="selectedPlayers.has(player.player_id)" class="pointer-events-none w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50">
                  </div>
                </div>
                
                <div class="grid grid-cols-3 gap-3 text-sm cursor-pointer" @click="togglePlayerExpansion(player.player_id)">
                  <div class="bg-gray-900/30 rounded p-2 border border-gray-700/50">
                    <p class="text-gray-500 text-[10px] uppercase mb-1 truncate">{{ t('activity.eventsAttended') }}</p>
                    <p><span class="font-bold text-gray-100 text-base">{{ player.total_events }}</span> <span class="text-gray-500 text-xs">/ {{ totalEvents }}</span></p>
                  </div>
                  <div class="bg-gray-900/30 rounded p-2 border border-gray-700/50">
                    <p class="text-gray-500 text-[10px] uppercase mb-1 truncate">{{ t('activity.attendance') }}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="font-mono text-sm font-bold" :class="{'text-green-400': (player.total_events / totalEvents) >= 0.8, 'text-yellow-400': (player.total_events / totalEvents) >= 0.5 && (player.total_events / totalEvents) < 0.8, 'text-red-400': (player.total_events / totalEvents) < 0.5}">
                        {{ totalEvents ? Math.round((player.total_events / totalEvents) * 100) : 0 }}%
                      </span>
                    </div>
                  </div>
                  <div class="bg-gray-900/30 rounded p-2 border border-gray-700/50">
                    <p class="text-gray-500 text-[10px] uppercase mb-1 truncate">{{ t('activity.weeklyActivity') }}</p>
                    <p><span class="font-bold text-blue-400 text-base">{{ player.weekly_game_activity || 0 }}</span></p>
                  </div>
                </div>
                
                <!-- Expanded Mobile View -->
                <div v-if="expandedPlayers.has(player.player_id)" class="mt-4 pt-4 border-t border-gray-700 animate-fade-in">
                   
                   <h4 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">{{ t('activity.weeklyActivityHistory') }}</h4>
                   <div class="space-y-2 mb-4">
                     <div v-for="wa in player.weekly_activity_history" :key="wa.week_id" class="bg-gray-900/50 border border-gray-700 rounded p-3 flex justify-between items-center gap-2">
                        <p class="text-sm font-medium text-gray-200 truncate">{{ wa.week_id }}</p>
                        <div class="flex items-center gap-2 shrink-0">
                          <p class="text-sm font-bold text-blue-400">{{ wa.score }}</p>
                          <p class="text-[10px] text-gray-500 font-mono">{{ new Date(wa.reported_at).toLocaleDateString() }}</p>
                        </div>
                     </div>
                     <p v-if="!player.weekly_activity_history || player.weekly_activity_history.length === 0" class="text-gray-500 italic text-xs">{{ t('activity.noActivity') }}</p>
                   </div>

                   <h4 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">{{ t('activity.eventsAttended') }}</h4>
                   <div class="space-y-2">
                     <div v-for="ev in player.events" :key="ev.event_id" class="bg-gray-900/50 border border-gray-700 rounded p-3 flex justify-between items-center gap-2">
                        <p class="text-sm font-medium text-gray-200 truncate">{{ ev.event_name }}</p>
                        <p class="text-xs text-gray-500 font-mono shrink-0">{{ new Date(ev.date).toLocaleDateString() }}</p>
                     </div>
                     <p v-if="!player.events || player.events.length === 0" class="text-gray-500 italic text-xs">{{ t('activity.noActivity') }}</p>
                   </div>
                </div>
              </div>
            </template>
            <div v-if="sortedActivities.length === 0" class="p-8 text-center text-gray-500 italic">{{ t('activity.noActivity') }}</div>
          </div>
          
          <!-- Desktop Table (Hidden on Mobile) -->
          <div class="hidden md:block overflow-x-auto">
            <table class="w-full text-left text-gray-300">
              <thead class="bg-gray-900 text-gray-400 uppercase text-xs tracking-wider">
              <tr>
                <th class="p-4 w-12 text-center">{{ t('activity.chart') }}</th>
                <th class="p-4">
                  <div class="flex flex-col gap-2">
                    <div class="cursor-pointer hover:text-white flex items-center w-max" @click="sortBy('player_name')">
                      {{ t('activity.playerName') }}
                      <span v-if="sortKey === 'player_name'" class="text-blue-400 ml-1">{{ sortDesc ? '↓' : '↑' }}</span>
                    </div>
                    <input type="text" v-model="playerSearchQuery" :placeholder="t('activity.searchPlayer')" class="bg-gray-800 border border-gray-700 text-gray-200 px-2 py-1 rounded outline-none focus:border-blue-500 font-normal normal-case w-full min-w-[120px] max-w-[200px]">
                  </div>
                </th>
                <th class="p-4 cursor-pointer hover:text-white align-top pt-5" @click="sortBy('total_events')">
                  <div class="flex items-center w-max">
                    {{ t('activity.eventsAttended') }}
                    <span v-if="sortKey === 'total_events'" class="text-blue-400 ml-1">{{ sortDesc ? '↓' : '↑' }}</span>
                  </div>
                </th>
                <th class="p-4 cursor-pointer hover:text-white align-top pt-5 min-w-[120px]" @click="sortBy('attendance')">
                  <div class="flex items-center w-max">
                    {{ t('activity.attendance') }}
                    <span v-if="sortKey === 'attendance'" class="text-blue-400 ml-1">{{ sortDesc ? '↓' : '↑' }}</span>
                  </div>
                </th>
                <th class="p-4 cursor-pointer hover:text-white align-top pt-5" @click="sortBy('weekly_game_activity')">
                  <div class="flex items-center w-max">
                    {{ t('activity.weeklyActivity') }}
                    <span v-if="sortKey === 'weekly_game_activity'" class="text-blue-400 ml-1">{{ sortDesc ? '↓' : '↑' }}</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <template v-for="player in sortedActivities" :key="player.player_id">
                <tr 
                  class="border-b border-gray-700/50 hover:bg-gray-750 transition-colors"
                  :class="{'bg-blue-900/10': selectedPlayers.has(player.player_id)}"
                >
                  <td class="p-4 text-center cursor-pointer" @click="togglePlayerSelection(player.player_id)">
                    <input type="checkbox" :checked="selectedPlayers.has(player.player_id)" class="pointer-events-none rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50">
                  </td>
                  <td class="p-4 font-medium cursor-pointer" @click="togglePlayerExpansion(player.player_id)">
                    <div class="flex items-center gap-2">
                      <svg class="w-4 h-4 text-gray-500 transition-transform" :class="{'rotate-180': expandedPlayers.has(player.player_id)}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                      {{ player.player_name }}
                      <svg v-if="!player.has_current_weekly_activity" class="w-4 h-4 text-red-500" title="Missing Weekly Activity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                    </div>
                  </td>
                  <td class="p-4 cursor-pointer" @click="togglePlayerExpansion(player.player_id)">
                    <span class="font-bold text-gray-100">{{ player.total_events }}</span>
                    <span class="text-gray-500 text-xs ml-1">/ {{ totalEvents }}</span>
                  </td>
                  <td class="p-4 cursor-pointer" @click="togglePlayerExpansion(player.player_id)">
                    <div class="flex items-center gap-3">
                      <span class="w-12 text-right font-mono text-sm" :class="{'text-green-400': (player.total_events / totalEvents) >= 0.8, 'text-yellow-400': (player.total_events / totalEvents) >= 0.5 && (player.total_events / totalEvents) < 0.8, 'text-red-400': (player.total_events / totalEvents) < 0.5}">
                        {{ totalEvents ? Math.round((player.total_events / totalEvents) * 100) : 0 }}%
                      </span>
                      <div class="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all" 
                          :class="{'bg-green-500': (player.total_events / totalEvents) >= 0.8, 'bg-yellow-500': (player.total_events / totalEvents) >= 0.5 && (player.total_events / totalEvents) < 0.8, 'bg-red-500': (player.total_events / totalEvents) < 0.5}"
                          :style="`width: ${totalEvents ? (player.total_events / totalEvents) * 100 : 0}%`"></div>
                      </div>
                    </div>
                  </td>
                  <td class="p-4 cursor-pointer" @click="togglePlayerExpansion(player.player_id)">
                    <span class="font-bold text-blue-400 font-mono">{{ player.weekly_game_activity || 0 }}</span>
                  </td>
                </tr>
                <!-- Expanded Player Details -->
                <tr v-if="expandedPlayers.has(player.player_id)" class="bg-gray-900/50 border-b border-gray-700/50">
                  <td colspan="5" class="p-4">
                    <div class="pl-10 space-y-6">
                      
                      <!-- Weekly Activity History -->
                      <div>
                        <h4 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">{{ t('activity.weeklyActivityHistory') }}</h4>
                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
                          <div v-for="wa in player.weekly_activity_history" :key="wa.week_id" class="bg-gray-800 border border-gray-700 rounded px-3 py-2 flex justify-between items-center gap-2">
                            <p class="text-sm font-medium text-gray-200 truncate">{{ wa.week_id }}</p>
                            <div class="flex items-center gap-3 shrink-0">
                              <p class="text-sm font-bold text-blue-400">{{ wa.score }}</p>
                              <p class="text-xs text-gray-500 font-mono">{{ new Date(wa.reported_at).toLocaleDateString() }}</p>
                            </div>
                          </div>
                        </div>
                        <p v-if="!player.weekly_activity_history || player.weekly_activity_history.length === 0" class="text-gray-500 italic text-xs mt-2">{{ t('activity.noActivity') }}</p>
                      </div>

                      <!-- Events Attended -->
                      <div>
                        <h4 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">{{ t('activity.eventsAttended') }}</h4>
                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
                          <div v-for="ev in player.events" :key="ev.event_id" class="bg-gray-800 border border-gray-700 rounded px-3 py-2 flex justify-between items-center gap-2">
                            <p class="text-sm font-medium text-gray-200 truncate" :title="ev.event_name">{{ ev.event_name }}</p>
                            <p class="text-xs text-gray-500 font-mono shrink-0">{{ new Date(ev.date).toLocaleDateString() }}</p>
                          </div>
                        </div>
                        <p v-if="!player.events || player.events.length === 0" class="text-gray-500 italic text-xs mt-2">{{ t('activity.noActivity') }}</p>
                      </div>

                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="sortedActivities.length === 0">
                <td colspan="5" class="p-8 text-center text-gray-500 italic">{{ t('activity.noActivity') }}</td>
              </tr>
            </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ELIGIBLE FOR DROP VIEW -->
      <div v-if="activeTab === 'eligible'" class="space-y-6 animate-fade-in">
        <div class="bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-700">
          <div class="p-4 bg-gray-900/50 border-b border-gray-700 flex justify-between items-center flex-wrap gap-4">
             <div>
               <h2 class="text-base sm:text-lg font-semibold text-gray-200">{{ t('activity.eligibleForDrop') }}</h2>
               <p class="text-xs text-gray-400 mt-1">{{ t('activity.eligibleRule').replace('{events}', dropConfig.min_events.toString()).replace('{score}', dropConfig.min_weekly_activity.toString()) }}</p>
             </div>
             <div class="flex items-center gap-2">
               <label class="text-sm text-gray-400">{{ t('activity.targetWeek') }}:</label>
               <select v-model="targetWeekId" @change="fetchActivity" class="bg-gray-800 text-gray-200 border border-gray-600 rounded px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none">
                 <option value="">Current Week</option>
                 <option v-for="week in availableWeeks" :key="week" :value="week">{{ week }}</option>
               </select>
             </div>
          </div>
          
          <!-- Mobile Deck (Cards) -->
          <div class="md:hidden p-4 space-y-4">
            <div v-for="player in [...sortedActivities].sort((a,b) => (b.is_eligible_for_drop ? 1 : 0) - (a.is_eligible_for_drop ? 1 : 0))" :key="player.player_id" class="bg-gray-800 border rounded-lg p-4 transition-colors" :class="player.is_eligible_for_drop ? 'border-green-500/50 bg-green-900/10' : 'border-red-500/30'">
              <div class="flex justify-between items-center mb-3">
                <span class="font-bold text-gray-100 text-lg truncate">{{ player.player_name }}</span>
                <span v-if="player.is_eligible_for_drop" class="bg-green-900 text-green-400 px-2 py-1 rounded text-xs font-bold flex items-center gap-1"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> {{ t('activity.eligible') }}</span>
                <span v-else class="bg-red-900 text-red-400 px-2 py-1 rounded text-xs font-bold flex items-center gap-1"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg> {{ t('activity.notEligible') }}</span>
              </div>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="bg-gray-900/30 rounded p-2 border border-gray-700/50">
                  <p class="text-gray-500 text-[10px] uppercase mb-1">{{ t('activity.recentPvp') }}</p>
                  <p class="font-bold text-gray-100 text-base" :class="{'text-green-400': player.recent_pvp_events >= dropConfig.min_events}">{{ player.recent_pvp_events || 0 }}</p>
                </div>
                <div class="bg-gray-900/30 rounded p-2 border border-gray-700/50">
                  <p class="text-gray-500 text-[10px] uppercase mb-1">{{ t('activity.weeklyScore') }}</p>
                  <p class="font-bold text-gray-100 text-base" :class="{'text-green-400': player.weekly_game_activity > dropConfig.min_weekly_activity}">{{ player.weekly_game_activity || 0 }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Desktop Table (Hidden on Mobile) -->
          <div class="hidden md:block overflow-x-auto">
            <table class="w-full text-left text-gray-300">
              <thead class="bg-gray-900 text-gray-400 uppercase text-xs tracking-wider">
                <tr>
                  <th class="p-4">{{ t('activity.playerName') }}</th>
                  <th class="p-4">{{ t('activity.recentPvp') }}</th>
                  <th class="p-4">{{ t('activity.weeklyScore') }}</th>
                  <th class="p-4">{{ t('activity.status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="player in [...sortedActivities].sort((a,b) => (b.is_eligible_for_drop ? 1 : 0) - (a.is_eligible_for_drop ? 1 : 0))" :key="player.player_id" class="border-b border-gray-700/50 hover:bg-gray-750 transition-colors">
                  <td class="p-4 font-medium text-gray-100">{{ player.player_name }}</td>
                  <td class="p-4 font-bold" :class="{'text-green-400': player.recent_pvp_events >= dropConfig.min_events}">{{ player.recent_pvp_events || 0 }}</td>
                  <td class="p-4 font-bold font-mono" :class="{'text-green-400': player.weekly_game_activity > dropConfig.min_weekly_activity}">{{ player.weekly_game_activity || 0 }}</td>
                  <td class="p-4">
                    <span v-if="player.is_eligible_for_drop" class="bg-green-900/50 text-green-400 px-3 py-1 rounded text-sm font-bold inline-flex items-center gap-1 border border-green-800"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> {{ t('activity.eligible') }}</span>
                    <span v-else class="bg-red-900/50 text-red-400 px-3 py-1 rounded text-sm font-bold inline-flex items-center gap-1 border border-red-800"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg> {{ t('activity.notEligible') }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- EVENT CENTRIC VIEW -->
      <div v-if="activeTab === 'event'" class="space-y-4 animate-fade-in">
        <div v-if="sortedEventsList.length === 0" class="text-center p-6 sm:p-10 text-gray-500 italic bg-gray-800 rounded-lg border border-gray-700">
          {{ t('activity.noEventsView') }}
        </div>
        
        <div v-for="event in sortedEventsList" :key="event.event_id" class="bg-gray-800 rounded-lg shadow border border-gray-700 overflow-hidden">
          <div 
            class="p-3 sm:p-4 bg-gray-800 hover:bg-gray-750 cursor-pointer flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0 transition-colors"
            @click="toggleEvent(event.event_id)"
          >
            <div>
              <h3 class="text-base sm:text-lg font-bold text-gray-200 break-words">{{ event.event_name }}</h3>
              <p class="text-xs sm:text-sm text-gray-400 font-mono mt-1 sm:mt-0">{{ new Date(event.date).toLocaleString() }}</p>
            </div>
            <div class="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
              <span class="bg-gray-900 border border-gray-700 px-2 sm:px-3 py-1 rounded text-xs sm:text-sm font-mono text-gray-300">
                <strong class="text-blue-400">{{ event.participants?.length || 0 }}</strong> {{ t('activity.participants') }}
              </span>
              <svg class="w-5 h-5 text-gray-500 transition-transform shrink-0" :class="{'rotate-180': expandedEvents.has(event.event_id)}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </div>
          
          <div v-if="expandedEvents.has(event.event_id)" class="p-3 sm:p-4 bg-gray-900/50 border-t border-gray-700">
            <div v-if="event.participants && event.participants.length > 0" class="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              <div v-for="p in event.participants" :key="p.player_id" class="bg-gray-800 border border-gray-700 rounded px-2 sm:px-3 py-2 text-xs sm:text-sm text-gray-300 flex items-center gap-2 truncate">
                <div class="w-1.5 sm:w-2 h-1.5 sm:h-2 rounded-full bg-green-500 shrink-0"></div>
                <span class="truncate">{{ p.player_name }}</span>
              </div>
            </div>
            <p v-else class="text-gray-500 italic text-xs sm:text-sm">{{ t('activity.noParticipants') }}</p>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.bg-gray-750 {
  background-color: rgba(31, 41, 55, 0.5); /* between gray-800 and gray-700 */
}
.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
