<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CyberModal from '../components/CyberModal.vue'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()

const userRole = ref<string>('user')
const username = ref<string>('')
const isLoading = ref(false)

const adminGuilds = ref<string[]>([])
const adminGuildsInfo = ref<any[]>([])
const adminGuildId = ref<string>('')
const pendingBuilds = ref<any[]>([])
const allBuilds = ref<any[]>([])
const dropHistory = ref<any[]>([])

// Filters
const filterText = ref('')
const filterStatus = ref('')
const filterPlayStyle = ref('')

const filteredBuilds = computed(() => {
  return allBuilds.value.filter(b => {
    // text filter (username, char name, class, or item name)
    let matchText = true
    if (filterText.value) {
      const q = filterText.value.toLowerCase()
      const uname = (b.user?.username || '').toLowerCase()
      const cname = (b.build?.character_name || '').toLowerCase()
      const cclass = (b.build?.character_class || '').toLowerCase()
      
      let itemMatch = false
      if (b.build?.slots) {
        itemMatch = Object.values(b.build.slots).some((item: any) => 
          item && item.name && item.name.toLowerCase().includes(q)
        )
      }
      
      matchText = uname.includes(q) || cname.includes(q) || cclass.includes(q) || itemMatch
    }
    
    // status filter
    let matchStatus = true
    if (filterStatus.value) {
      matchStatus = b.build?.status === filterStatus.value
    }
    
    // style filter
    let matchStyle = true
    if (filterPlayStyle.value) {
      matchStyle = b.build?.play_style === filterPlayStyle.value
    }
    
    return matchText && matchStatus && matchStyle
  })
})

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

const showConfirm = (message: string, title = 'CONFIRM ACTION'): Promise<boolean> => {
  return new Promise((resolve) => {
    modalState.value = {
      show: true,
      title,
      message,
      isConfirm: true,
      hasInput: false,
      inputValue: '',
      resolve
    }
  })
}

const promptInput = (message: string, title = 'INPUT REQUIRED'): Promise<string | null> => {
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
    if (modalState.value.hasInput) {
      modalState.value.resolve(modalState.value.inputValue)
    } else {
      modalState.value.resolve(true)
    }
  }
  modalState.value.show = false
}

const handleModalCancel = () => {
  if (modalState.value.resolve) {
    if (modalState.value.hasInput) {
      modalState.value.resolve(null)
    } else {
      modalState.value.resolve(false)
    }
  }
  modalState.value.show = false
}

// Drops Api Functions
const fetchPendingBuilds = async () => {
  if (!adminGuildId.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/admin/guilds/${adminGuildId.value}/builds/pending`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) pendingBuilds.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const fetchDropHistory = async () => {
  if (!adminGuildId.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${adminGuildId.value}/history`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) dropHistory.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const fetchAllBuilds = async () => {
  if (!adminGuildId.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/admin/guilds/${adminGuildId.value}/builds`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) allBuilds.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const activePolls = ref<any[]>([])

const fetchPolls = async () => {
  if (!adminGuildId.value) return
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${adminGuildId.value}/polls`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      activePolls.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

const onGuildChange = () => {
  fetchPendingBuilds()
  fetchAllBuilds()
  fetchDropHistory()
  fetchPolls()
}

const approveBuild = async (buildId: string) => {
  if (!(await showConfirm("Approvare questa build come Primaria?", "CONFERMA"))) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/admin/guilds/${adminGuildId.value}/builds/${buildId}/approve`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      showAlert(t('drops.approveSuccess'), "SUCCESS")
      fetchPendingBuilds()
      fetchAllBuilds()
    } else {
      showAlert(t('drops.approveError'), "ERROR")
    }
  } catch(e) {
    showAlert(t('drops.approveError'), "ERROR")
  } finally { isLoading.value = false }
}

const assignPoll = async (pollId: string, userId: string, category: string) => {
  if (!(await showConfirm(t('drops.assignConfirm'), "CONFERMA"))) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${adminGuildId.value}/polls/${pollId}/assign`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, category })
    })
    if (res.ok) {
      showAlert(t('drops.dropAssignedSuccess'), "SUCCESS")
      fetchPolls()
      fetchDropHistory()
    } else {
      showAlert(t('drops.assignError'), "ERROR")
    }
  } catch(e) {
    showAlert(t('drops.networkError'), "ERROR")
  } finally { isLoading.value = false }
}

const removeCandidate = async (pollId: string, userId: string) => {
  if (!(await showConfirm(t('drops.removeCandidateConfirm'), "CONFERMA"))) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${adminGuildId.value}/polls/${pollId}/candidates/${userId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      fetchPolls()
    }
  } catch(e) {} finally { isLoading.value = false }
}

const cancelPoll = async (pollId: string) => {
  if (!(await showConfirm("Sei sicuro di voler annullare questo sondaggio? Nessun drop verrà assegnato.", "ANNULLA SONDAGGIO"))) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${adminGuildId.value}/polls/${pollId}/cancel`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      fetchPolls()
    }
  } catch(e) {} finally { isLoading.value = false }
}

const addCandidate = async (pollId: string) => {
  const userId = await promptInput(t('drops.addCandidatePrompt'))
  if (!userId) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/guilds/${adminGuildId.value}/polls/${pollId}/candidates`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${sessionToken.value}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })
    if (res.ok) {
      fetchPolls()
    }
  } catch(e) {} finally { isLoading.value = false }
}

const userModalState = ref({
  show: false,
  user: null as any,
  build: null as any,
  history: [] as any[]
})

const openUserDetails = (discordId: string, username: string, avatar: string | null = null) => {
  // Find primary build
  const userBuilds = allBuilds.value.filter(b => b.user.discord_id === discordId && b.build.status === 'primary')
  const build = userBuilds.length > 0 ? userBuilds[0].build : null
  
  // Find drop history
  const history = dropHistory.value.filter(h => h.user_id === discordId).sort((a, b) => new Date(b.assigned_at).getTime() - new Date(a.assigned_at).getTime())

  userModalState.value = {
    show: true,
    user: { discord_id: discordId, username, avatar },
    build,
    history
  }
}

const closeUserDetails = () => {
  userModalState.value.show = false
}

const initDropsAdmin = async () => {
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/me`, { headers: { 'Authorization': `Bearer ${sessionToken.value}` } })
    if (res.ok) {
      const data = await res.json()
      userRole.value = data.role
      username.value = data.username
      adminGuilds.value = data.guilds || []
      adminGuildsInfo.value = data.guilds_info || []
      
      if (adminGuilds.value.length > 0) {
        adminGuildId.value = adminGuilds.value[0]
        onGuildChange()
      }
    }
  } catch(e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  if (!sessionToken.value) {
    router.replace({ name: 'Login' })
    return
  }
  
  try {
    const base64Url = sessionToken.value.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join('')))
    
    if (payload) {
      userRole.value = payload.role || 'user'
      username.value = payload.username || 'Agent'
    }

    if (userRole.value === 'user') {
      router.replace({ name: 'Dashboard' })
      return
    }

    initDropsAdmin()
  } catch (e) {
    router.replace({ name: 'Login' })
  }
})
</script>

<template>
  <div class="p-4 md:p-8 max-w-7xl mx-auto animate-fade-in">
    <div class="flex flex-col sm:flex-row justify-between items-center mb-8 border-b border-gray-800 pb-4 gap-4 text-center sm:text-left">
      <h2 class="font-rajdhani text-3xl font-bold text-cyber-purple tracking-wider uppercase">{{ t('drops.management') }}</h2>
      <button @click="$router.push('/')" class="text-sm text-gray-500 hover:text-cyber-cyan transition-colors font-mono">
        {{ t('app.backToHub') }}
      </button>
    </div>

      <!-- Modale Cyberpunk Globale -->
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

      <!-- Modale Dettagli Utente -->
      <Teleport to="body">
        <div v-if="userModalState.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div class="glass-panel p-6 max-w-2xl w-full border-t-4 border-cyber-purple shadow-[0_0_20px_rgba(188,19,254,0.2)] max-h-[90vh] overflow-y-auto custom-scrollbar">
            <div class="flex justify-between items-start mb-6">
              <div class="flex items-center gap-4">
                <img v-if="userModalState.user?.avatar" :src="`https://cdn.discordapp.com/avatars/${userModalState.user.discord_id}/${userModalState.user.avatar}.png`" class="w-16 h-16 rounded-full border-2 border-cyber-purple">
                <div v-else class="w-16 h-16 rounded-full bg-gray-800 border-2 border-cyber-purple flex items-center justify-center">
                  <span class="text-2xl font-bold text-gray-400">{{ userModalState.user?.username?.charAt(0) || '?' }}</span>
                </div>
                <div>
                  <h3 class="font-orbitron text-2xl text-cyber-cyan">{{ userModalState.user?.username }}</h3>
                  <p class="text-gray-500 font-mono text-sm">ID: {{ userModalState.user?.discord_id }}</p>
                </div>
              </div>
              <button @click="closeUserDetails" class="text-gray-500 hover:text-white">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>

            <!-- Build Primaria -->
            <div class="mb-8">
              <h4 class="font-rajdhani text-xl text-yellow-500 mb-3 border-b border-gray-700 pb-1 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path></svg>
                {{ t('drops.primaryBuild') }}
              </h4>
              <div v-if="userModalState.build" class="bg-gray-800/50 p-4 rounded border border-gray-700">
                <div class="flex flex-wrap gap-3 mb-4">
                  <span v-if="userModalState.build.character_name" class="px-3 py-1 bg-gray-900 border border-gray-700 rounded text-sm font-mono text-gray-300">
                    <strong class="text-cyber-cyan">{{ userModalState.build.character_name }}</strong>
                  </span>
                  <span v-if="userModalState.build.character_class" class="px-3 py-1 bg-gray-900 border border-gray-700 rounded text-sm font-mono text-gray-300">
                    <strong class="text-cyber-purple">{{ userModalState.build.character_class }}</strong>
                  </span>
                  <span v-if="userModalState.build.play_style" class="px-3 py-1 bg-gray-900 border border-gray-700 rounded text-sm font-mono font-bold text-gray-300">
                    {{ userModalState.build.play_style }}
                  </span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm font-mono text-gray-400">
                  <div v-for="(item, slotKey) in userModalState.build.slots" :key="slotKey" class="truncate border-b border-gray-700/50 pb-1">
                    <span class="text-gray-500 capitalize">{{ String(slotKey).replace('_', ' ') }}:</span> 
                    <span v-if="item" class="text-gray-200 ml-1" :title="item.name">{{ item.name }}</span>
                    <span v-else class="text-red-900/50 italic ml-1">{{ t('drops.empty') }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="text-gray-500 italic">
                {{ t('drops.noBuildFound') }}
              </div>
            </div>

            <!-- Storico Drop -->
            <div>
              <h4 class="font-rajdhani text-xl text-green-500 mb-3 border-b border-gray-700 pb-1 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                {{ t('drops.pastDrops') }} ({{ userModalState.history.length }})
              </h4>
              <div v-if="userModalState.history.length > 0" class="space-y-2 max-h-48 overflow-y-auto custom-scrollbar pr-2">
                <div v-for="h in userModalState.history" :key="h._id" class="bg-gray-900/50 border border-gray-700 p-3 rounded flex justify-between items-center">
                  <div>
                    <div class="text-cyber-cyan font-bold">{{ h.item_name }}</div>
                    <div class="text-xs text-gray-500 font-mono">{{ new Date(h.assigned_at).toLocaleString() }}</div>
                  </div>
                  <span class="text-xs font-mono text-gray-400 uppercase">{{ h.category }}</span>
                </div>
              </div>
              <div v-else class="text-gray-500 italic">
                {{ t('drops.noAssignmentHistory') }}
              </div>
            </div>
            
            <div class="mt-8 flex justify-end">
              <button @click="closeUserDetails" class="px-6 py-2 bg-gray-800 hover:bg-gray-700 text-white font-orbitron rounded border border-gray-600 transition-colors">
                {{ t('drops.close') }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>

    <div v-if="adminGuilds.length === 0 && !isLoading" class="glass-panel p-6 rounded-xl text-center">
      <p class="text-gray-400 font-mono">{{ t('drops.noAuthorizedGuild') }}</p>
    </div>
    
    <div v-else>
      <!-- Mostra la tendina solo se c'è più di una gilda -->
      <div v-if="adminGuilds.length > 1" class="bg-gray-900/50 border border-gray-800 p-6 rounded mb-6 flex flex-col md:flex-row gap-4 md:items-center">
        <label class="font-rajdhani text-gray-400 uppercase tracking-wide">{{ t('drops.selectGuildToManage') }}</label>
        <select v-model="adminGuildId" @change="onGuildChange" class="neon-input bg-gray-900 w-full md:w-1/3">
          <option v-for="g in adminGuildsInfo" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
      </div>

      <!-- Mostra un'intestazione se c'è una sola gilda -->
      <div v-if="adminGuilds.length === 1" class="bg-gray-900/50 border border-gray-800 p-6 rounded mb-6 flex items-center gap-4">
        <div class="w-12 h-12 rounded-full border border-gray-700 overflow-hidden flex items-center justify-center bg-gray-800">
          <img v-if="adminGuildsInfo[0]?.icon" :src="`https://cdn.discordapp.com/icons/${adminGuildId}/${adminGuildsInfo[0].icon}.png`" class="w-full h-full object-cover">
          <span v-else class="text-gray-400 font-bold">{{ adminGuildsInfo[0]?.name?.charAt(0) || 'G' }}</span>
        </div>
        <div>
          <h3 class="font-rajdhani text-xl text-gray-200 font-bold uppercase">{{ adminGuildsInfo[0]?.name }}</h3>
          <p class="text-gray-500 font-mono text-sm">{{ t('drops.singleGuildSelected') }}</p>
        </div>
      </div>

      <div v-if="adminGuildId">
        
        <div class="flex justify-end mb-4">
          <button @click="onGuildChange" class="px-4 py-2 bg-gray-900/50 hover:bg-gray-800 text-cyber-cyan font-orbitron text-sm rounded border border-cyber-cyan/30 transition-colors flex items-center gap-2 shadow-[0_0_10px_rgba(0,255,255,0.1)]">
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
                <h4 class="text-cyber-cyan font-bold font-rajdhani text-lg mb-2">{{ poll.item_name }}</h4>
                <div class="mb-4">
                  <p class="text-xs text-gray-400 mb-2 uppercase tracking-wide border-b border-gray-700 pb-1 flex justify-between">
                    <span>{{ t('drops.candidates') }} ({{ poll.candidates_info?.length || 0 }})</span>
                    <button @click="addCandidate(poll.id)" class="text-cyber-cyan hover:text-white transition-colors" :title="t('drops.addUser')">+ ADD</button>
                  </p>
                  <ul class="space-y-1 max-h-32 overflow-y-auto custom-scrollbar pr-2">
                    <li v-for="c in poll.candidates_info" :key="c.discord_id" class="flex justify-between items-center text-sm bg-gray-900/50 p-1.5 rounded border border-gray-800">
                      <div class="flex items-center">
                        <span @click="openUserDetails(c.discord_id, c.username)" class="text-gray-300 truncate mr-2 cursor-pointer hover:text-cyber-cyan hover:underline transition-colors">{{ c.username }}</span>
                        <span class="text-[10px] uppercase border border-gray-700 text-gray-400 px-1 rounded">{{ c.reason }}</span>
                      </div>
                      <div class="flex gap-2">
                        <button @click="assignPoll(poll.id, c.discord_id, c.reason && c.reason !== 'Sconosciuta' ? c.reason : 'manual')" class="text-green-400 hover:text-green-300 text-xs px-2 py-0.5 border border-green-400/30 rounded bg-green-900/20">{{ t('drops.wins') }}</button>
                        <button @click="removeCandidate(poll.id, c.discord_id)" class="text-red-400 hover:text-red-300 text-xs px-2 py-0.5 border border-red-400/30 rounded bg-red-900/20">X</button>
                      </div>
                    </li>
                    <li v-if="!poll.candidates_info || poll.candidates_info.length === 0" class="text-xs text-gray-500 italic">{{ t('drops.noCandidates') }}</li>
                  </ul>
                </div>
              </div>
              <div class="flex justify-between items-center text-xs text-gray-500 font-mono mt-2 pt-2 border-t border-gray-800">
                <span>{{ t('drops.pollId') }} {{ poll.id }}</span>
                <button @click="cancelPoll(poll.id)" class="text-red-500 hover:text-red-400 hover:underline">Annulla</button>
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- PENDING BUILDS -->
        <div class="bg-gray-900/50 border border-gray-800 rounded p-6">
          <h3 class="font-rajdhani text-xl text-yellow-500 mb-4 font-bold flex items-center gap-2">
            {{ t('drops.pendingBuilds') }}
          </h3>
          <div v-if="isLoading" class="text-gray-500 font-mono animate-pulse">{{ t('drops.loadingDrops') }}</div>
          <div v-else-if="pendingBuilds.length === 0" class="text-gray-500 italic text-sm">{{ t('drops.noPendingBuilds') }}</div>
          <div v-else class="space-y-4 max-h-96 overflow-y-auto custom-scrollbar pr-2">
            <div v-for="b in pendingBuilds" :key="b.build._id" class="border border-gray-700 bg-gray-800/30 p-4 rounded">
              <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 gap-3 sm:gap-0">
                <div class="flex items-center gap-2">
                  <img v-if="b.user.avatar" :src="`https://cdn.discordapp.com/avatars/${b.user.discord_id}/${b.user.avatar}.png`" class="w-8 h-8 rounded-full">
                  <span @click="openUserDetails(b.user.discord_id, b.user.username, b.user.avatar)" class="text-cyber-cyan font-bold cursor-pointer hover:underline">{{ b.user.username }}</span>
                </div>
                <button @click="approveBuild(b.build._id)" class="w-full sm:w-auto text-xs bg-green-900/40 hover:bg-green-800 text-green-200 px-3 py-1.5 rounded transition-colors font-bold border border-green-700/50">
                  {{ t('drops.approveAsPrimary').toUpperCase() }}
                </button>
              </div>
              <div class="mb-3 flex flex-wrap gap-2">
                <span v-if="b.build.character_name" class="px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs font-mono text-gray-300">
                  {{ t('drops.characterName') }}: <strong class="text-cyber-cyan">{{ b.build.character_name }}</strong>
                </span>
                <span v-if="b.build.character_class" class="px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs font-mono text-gray-300">
                  {{ t('drops.characterClass') }}: <strong class="text-cyber-purple">{{ b.build.character_class }}</strong>
                </span>
                <span v-if="b.build.play_style" class="px-2 py-1 rounded text-xs font-mono font-bold" 
                  :class="{
                    'bg-red-900/40 text-red-400 border border-red-700/50': b.build.play_style === 'PvP',
                    'bg-blue-900/40 text-blue-400 border border-blue-700/50': b.build.play_style === 'PvE',
                    'bg-purple-900/40 text-purple-400 border border-purple-700/50': b.build.play_style === 'PvPxPvE'
                  }">
                  {{ b.build.play_style }}
                </span>
                <a v-if="b.build.questlog_url" :href="b.build.questlog_url" target="_blank" class="px-2 py-1 bg-indigo-900/40 hover:bg-indigo-900/80 border border-indigo-700/50 rounded text-xs font-mono text-indigo-300 flex items-center gap-1 transition-colors">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                  Questlog
                </a>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono text-gray-400 border-t border-gray-700/50 pt-3">
                <div v-for="(item, slotKey) in b.build.slots" :key="slotKey">
                  <span class="text-gray-500 capitalize">{{ String(slotKey).replace('_', ' ') }}:</span> 
                  <span v-if="item" class="text-gray-300 ml-1">{{ item.name }}</span>
                  <span v-else class="text-red-900/50 italic ml-1">{{ t('drops.empty') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- DROP HISTORY -->
        <div class="bg-gray-900/50 border border-gray-800 rounded p-6">
          <h3 class="font-rajdhani text-xl text-cyber-purple mb-4 font-bold flex items-center gap-2">
            {{ t('drops.assignmentHistory') }}
          </h3>
          <div v-if="isLoading" class="text-gray-500 font-mono animate-pulse">{{ t('drops.loadingDrops') }}</div>
          <div v-else-if="dropHistory.length === 0" class="text-gray-500 italic text-sm">{{ t('drops.noAssignmentHistory') }}</div>
          <div v-else class="space-y-2 max-h-96 overflow-y-auto custom-scrollbar pr-2">
            <div v-for="h in dropHistory" :key="h._id" class="flex justify-between items-center border-b border-gray-800/50 py-2">
              <div class="flex flex-col">
                <span class="text-gray-200 font-bold text-sm">{{ h.item_name }}</span>
                <span @click="openUserDetails(h.user_id, h.user?.username || h.user_id, h.user?.avatar)" class="text-cyber-cyan text-xs font-mono cursor-pointer hover:underline">Utente: {{ h.user?.username || h.user_id }}</span>
              </div>
              <div class="flex flex-col items-end">
                <span class="text-gray-500 text-xs">{{ new Date(h.assigned_at).toLocaleDateString() }}</span>
                <span class="text-xs bg-gray-800 px-2 py-0.5 rounded text-gray-400">{{ h.category }}</span>
              </div>
            </div>
          </div>
        </div>
        <!-- ALL BUILDS -->
        <div class="bg-gray-900/50 border border-gray-800 rounded p-6 lg:col-span-2 mt-2">
          <h3 class="font-rajdhani text-xl text-cyber-cyan mb-4 font-bold flex items-center gap-2">
            Tutte le Build della Gilda
          </h3>
          
          <!-- Filters -->
          <div class="flex flex-col md:flex-row gap-4 mb-6 bg-gray-800/30 p-4 rounded border border-gray-700">
            <div class="flex-1">
              <label class="block text-xs font-mono text-gray-400 mb-1">Cerca (Nome/Classe/Oggetto)</label>
              <input type="text" v-model="filterText" class="neon-input w-full text-sm" placeholder="Es. Spadone, NyxPlayer..." />
            </div>
            <div class="w-full md:w-48">
              <label class="block text-xs font-mono text-gray-400 mb-1">{{ t('drops.status') }}</label>
              <select v-model="filterStatus" class="neon-input w-full text-sm">
                <option value="">{{ t('drops.allFilter') }}</option>
                <option value="primary">Primary</option>
                <option value="pending">Pending</option>
                <option value="draft">Draft</option>
              </select>
            </div>
            <div class="w-full md:w-48">
              <label class="block text-xs font-mono text-gray-400 mb-1">{{ t('drops.playStyle') }}</label>
              <select v-model="filterPlayStyle" class="neon-input w-full text-sm">
                <option value="">{{ t('drops.allFilter') }}</option>
                <option value="PvP">PvP</option>
                <option value="PvE">PvE</option>
                <option value="PvPxPvE">PvP & PvE</option>
              </select>
            </div>
          </div>

          <div v-if="isLoading && allBuilds.length === 0" class="text-gray-500 font-mono animate-pulse">{{ t('drops.loadingDrops') }}</div>
          <div v-else-if="filteredBuilds.length === 0" class="text-gray-500 italic text-sm">{{ t('drops.noBuildsFound') }}</div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto custom-scrollbar pr-2">
            <div v-for="b in filteredBuilds" :key="b.build._id" class="border border-gray-700 bg-gray-800/30 p-4 rounded flex flex-col h-full">
              <!-- Header Card -->
              <div class="flex justify-between items-start mb-3">
                <div class="flex items-center gap-2">
                  <img v-if="b.user?.avatar" :src="`https://cdn.discordapp.com/avatars/${b.user.discord_id}/${b.user.avatar}.png`" class="w-8 h-8 rounded-full">
                  <span @click="openUserDetails(b.user.discord_id, b.user.username, b.user.avatar)" class="text-cyber-cyan font-bold truncate max-w-[120px] cursor-pointer hover:underline">{{ b.user?.username }}</span>
                </div>
                <span class="px-2 py-1 rounded text-xs font-mono font-bold uppercase"
                  :class="{
                    'bg-green-900/40 text-green-400 border border-green-700/50': b.build.status === 'primary',
                    'bg-yellow-900/40 text-yellow-400 border border-yellow-700/50': b.build.status === 'pending',
                    'bg-gray-800 text-gray-400 border border-gray-600/50': b.build.status === 'draft'
                  }">
                  {{ b.build.status }}
                </span>
              </div>
              
              <!-- Character Info -->
              <div class="mb-3 flex flex-wrap gap-2 flex-grow-0">
                <span v-if="b.build.character_name" class="px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs font-mono text-gray-300 truncate max-w-[150px]" :title="b.build.character_name">
                  <strong class="text-cyber-cyan">{{ b.build.character_name }}</strong>
                </span>
                <span v-if="b.build.character_class" class="px-2 py-1 bg-gray-900 border border-gray-700 rounded text-xs font-mono text-gray-300 truncate max-w-[150px]" :title="b.build.character_class">
                  <strong class="text-cyber-purple">{{ b.build.character_class }}</strong>
                </span>
                <span v-if="b.build.play_style" class="px-2 py-1 rounded text-xs font-mono font-bold" 
                  :class="{
                    'bg-red-900/40 text-red-400 border border-red-700/50': b.build.play_style === 'PvP',
                    'bg-blue-900/40 text-blue-400 border border-blue-700/50': b.build.play_style === 'PvE',
                    'bg-purple-900/40 text-purple-400 border border-purple-700/50': b.build.play_style === 'PvPxPvE'
                  }">
                  {{ b.build.play_style }}
                </span>
                <a v-if="b.build.questlog_url" :href="b.build.questlog_url" target="_blank" class="px-2 py-1 bg-indigo-900/40 hover:bg-indigo-900/80 border border-indigo-700/50 rounded text-xs font-mono text-indigo-300 flex items-center gap-1 transition-colors">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                  Questlog
                </a>
              </div>

              <!-- Slots compatti -->
              <div class="mt-auto grid grid-cols-1 sm:grid-cols-2 gap-1 text-[10px] sm:text-xs font-mono text-gray-400 border-t border-gray-700/50 pt-3">
                <div v-for="(item, slotKey) in b.build.slots" :key="slotKey" class="truncate">
                  <span class="text-gray-500 capitalize">{{ String(slotKey).replace('_', ' ') }}:</span> 
                  <span v-if="item" class="text-gray-300 ml-1 truncate" :title="item.name">{{ item.name }}</span>
                  <span v-else class="text-red-900/50 italic ml-1">{{ t('drops.empty') }}</span>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>
      </div> <!-- End of grid grid-cols-1 lg:grid-cols-2 gap-6 -->
    </div> <!-- End of v-if adminGuildId -->
  </div> <!-- End of glass-panel container -->
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(17, 24, 39, 0.5);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(107, 114, 128, 0.8);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 1);
}
</style>
