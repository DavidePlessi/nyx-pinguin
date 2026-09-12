<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
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

const activities = ref<any[]>([])
const eventsList = ref<any[]>([])
const weeklyData = ref<Record<string, any>>({})
const totalEvents = ref(0)

const activeTab = ref('player') // 'player' or 'event'
const expandedEvents = ref<Set<string>>(new Set())

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

// Chart color palette
const colors = [
  '#4ade80', '#60a5fa', '#f472b6', '#fbbf24', '#a78bfa',
  '#2dd4bf', '#fb923c', '#f87171', '#38bdf8', '#c0caf5'
]

const fetchActivity = async () => {
  if (!adminGuildId.value) return
  loading.value = true
  try {
    let url = `${BACKEND_URL}/api/activity/${adminGuildId.value}?`
    if (fromDate.value) url += `from_date=${new Date(fromDate.value).toISOString()}&`
    if (toDate.value) {
      let tDate = new Date(toDate.value)
      tDate.setHours(23, 59, 59, 999)
      url += `to_date=${tDate.toISOString()}`
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
      
      // Auto-select top 5 players for chart if none selected
      if (selectedPlayers.value.size === 0 && activities.value.length > 0) {
        const top5 = [...activities.value].sort((a, b) => b.total_events - a.total_events).slice(0, 5)
        top5.forEach(p => selectedPlayers.value.add(p.player_id))
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
      alert('Sync failed: ' + (data.detail || 'Unknown error'))
    }
  } catch (err) {
    console.error('Failed to sync', err)
    alert('Network error')
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

const sortedActivities = computed(() => {
  return [...activities.value].sort((a, b) => {
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

const toggleEvent = (eventId: string) => {
  if (expandedEvents.value.has(eventId)) {
    expandedEvents.value.delete(eventId)
  } else {
    expandedEvents.value.add(eventId)
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
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
      <h1 class="text-3xl font-bold text-gray-100 uppercase tracking-wide">Activity Tracking</h1>
      
      <div class="flex items-center gap-4">
        <!-- Date Filters -->
        <div class="flex items-center gap-2">
          <input type="date" v-model="fromDate" class="bg-gray-800 border border-gray-700 text-gray-300 px-3 py-1 rounded outline-none focus:border-blue-500 text-sm">
          <span class="text-gray-500">to</span>
          <input type="date" v-model="toDate" class="bg-gray-800 border border-gray-700 text-gray-300 px-3 py-1 rounded outline-none focus:border-blue-500 text-sm">
        </div>

        <button 
          v-if="['admin', 'guild_admin'].includes(userRole)"
          @click="forceSync" 
          :disabled="syncing || !adminGuildId"
          class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded font-medium disabled:opacity-50 flex items-center gap-2"
        >
          <svg class="w-4 h-4" :class="{'animate-spin': syncing}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          {{ syncing ? 'Syncing...' : 'Force Sync Now' }}
        </button>
      </div>
    </div>

    <!-- Guild Selector -->
    <div v-if="adminGuilds.length > 1" class="bg-gray-800 p-4 rounded mb-6 flex flex-col md:flex-row gap-4 md:items-center">
      <label class="font-rajdhani text-gray-400 uppercase tracking-wide">Select Guild</label>
      <select v-model="adminGuildId" @change="onGuildChange" class="bg-gray-900 border border-gray-700 text-white px-3 py-2 rounded w-full md:w-1/3 outline-none focus:border-blue-500">
        <option v-for="g in adminGuildsInfo" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
    </div>
    
    <div v-if="loading" class="text-center py-10 text-gray-400 font-mono animate-pulse">Loading data...</div>
    <div v-else-if="!adminGuildId" class="text-center py-10 text-gray-500">No guilds available.</div>
    <div v-else class="space-y-6">
      
      <!-- Tabs -->
      <div class="flex border-b border-gray-700">
        <button 
          @click="activeTab = 'player'" 
          class="px-6 py-3 font-semibold text-sm transition-colors border-b-2"
          :class="activeTab === 'player' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          Player Centric
        </button>
        <button 
          @click="activeTab = 'event'" 
          class="px-6 py-3 font-semibold text-sm transition-colors border-b-2"
          :class="activeTab === 'event' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          Event Centric
        </button>
      </div>

      <!-- PLAYER CENTRIC VIEW -->
      <div v-if="activeTab === 'player'" class="space-y-6 animate-fade-in">
        <!-- Chart -->
        <div class="bg-gray-800 rounded-lg shadow p-6 border border-gray-700">
          <h2 class="text-xl font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
            Temporal Participation Trends
          </h2>
          <div style="height: 350px;">
            <Line v-if="chartData.labels.length > 0 && selectedPlayers.size > 0" :data="chartData" :options="chartOptions" />
            <div v-else class="text-gray-500 h-full flex items-center justify-center italic">
              {{ chartData.labels.length === 0 ? 'No events found in this date range.' : 'Select at least one player below to show the chart.' }}
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-4 text-center">Click on table rows below to add or remove players from this chart.</p>
        </div>

        <!-- Summary & Table -->
        <div class="bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-700">
          <div class="p-4 bg-gray-900/50 border-b border-gray-700 flex justify-between items-center">
            <h2 class="text-lg font-semibold text-gray-200">Participation Roster</h2>
            <div class="text-sm font-mono text-gray-400">Total Events in period: <strong class="text-white">{{ totalEvents }}</strong></div>
          </div>
          
          <div class="overflow-x-auto">
            <table class="w-full text-left text-gray-300">
              <thead class="bg-gray-900 text-gray-400 uppercase text-xs tracking-wider">
                <tr>
                  <th class="p-4 w-12 text-center">Chart</th>
                  <th class="p-4 cursor-pointer hover:text-white" @click="sortBy('player_name')">
                    Player Name
                    <span v-if="sortKey === 'player_name'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
                  </th>
                  <th class="p-4 cursor-pointer hover:text-white" @click="sortBy('total_events')">
                    Events Attended
                    <span v-if="sortKey === 'total_events'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
                  </th>
                  <th class="p-4 cursor-pointer hover:text-white" @click="sortBy('attendance')">
                    Attendance %
                    <span v-if="sortKey === 'attendance'" class="text-blue-400">{{ sortDesc ? '↓' : '↑' }}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="player in sortedActivities" 
                  :key="player.player_id" 
                  class="border-b border-gray-700/50 hover:bg-gray-750 cursor-pointer transition-colors"
                  :class="{'bg-blue-900/10': selectedPlayers.has(player.player_id)}"
                  @click="togglePlayerSelection(player.player_id)"
                >
                  <td class="p-4 text-center">
                    <input type="checkbox" :checked="selectedPlayers.has(player.player_id)" class="pointer-events-none rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500/50">
                  </td>
                  <td class="p-4 font-medium">{{ player.player_name }}</td>
                  <td class="p-4">
                    <span class="font-bold text-gray-100">{{ player.total_events }}</span>
                    <span class="text-gray-500 text-xs ml-1">/ {{ totalEvents }}</span>
                  </td>
                  <td class="p-4">
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
                </tr>
                <tr v-if="sortedActivities.length === 0">
                  <td colspan="4" class="p-8 text-center text-gray-500 italic">No activity recorded for this date range.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- EVENT CENTRIC VIEW -->
      <div v-if="activeTab === 'event'" class="space-y-4 animate-fade-in">
        <div v-if="sortedEventsList.length === 0" class="text-center p-10 text-gray-500 italic bg-gray-800 rounded-lg border border-gray-700">
          No events found in this date range.
        </div>
        
        <div v-for="event in sortedEventsList" :key="event.event_id" class="bg-gray-800 rounded-lg shadow border border-gray-700 overflow-hidden">
          <div 
            class="p-4 bg-gray-800 hover:bg-gray-750 cursor-pointer flex justify-between items-center transition-colors"
            @click="toggleEvent(event.event_id)"
          >
            <div>
              <h3 class="text-lg font-bold text-gray-200">{{ event.event_name }}</h3>
              <p class="text-sm text-gray-400 font-mono">{{ new Date(event.date).toLocaleString() }}</p>
            </div>
            <div class="flex items-center gap-4">
              <span class="bg-gray-900 border border-gray-700 px-3 py-1 rounded text-sm font-mono text-gray-300">
                <strong class="text-blue-400">{{ event.participants?.length || 0 }}</strong> participants
              </span>
              <svg class="w-5 h-5 text-gray-500 transition-transform" :class="{'rotate-180': expandedEvents.has(event.event_id)}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </div>
          
          <div v-if="expandedEvents.has(event.event_id)" class="p-4 bg-gray-900/50 border-t border-gray-700">
            <div v-if="event.participants && event.participants.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              <div v-for="p in event.participants" :key="p.player_id" class="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-green-500"></div>
                {{ p.player_name }}
              </div>
            </div>
            <p v-else class="text-gray-500 italic text-sm">No valid participants recorded for this event.</p>
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
