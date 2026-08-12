<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import CyberModal from '../components/CyberModal.vue'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()

const activeTab = ref('overview') // 'overview', 'users', 'system'

const isLoading = ref(false)
//const error = ref('')

const stats = ref({
  total_users: 0,
  total_configs: 0,
  active_configs: 0
})

const users = ref<any[]>([])
const logs = ref<any[]>([])
let logsInterval: any = null

const modalState = ref({
  show: false,
  title: 'SYSTEM ALERT',
  message: '',
  isConfirm: false,
  resolve: null as ((value: boolean) => void) | null
})

// New user form state
const newUserForm = ref({
  discord_id: '',
  username: '',
  role: 'user'
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

const logout = () => {
  localStorage.removeItem('dab_session_token')
  sessionToken.value = null
  if (logsInterval) clearInterval(logsInterval)
  router.replace({ name: 'Login' })
}

const fetchStats = async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/api/admin/stats`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) stats.value = await res.json()
  } catch (e) {
    console.error("Failed to fetch stats", e)
  }
}

const fetchUsers = async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/api/admin/users`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) users.value = await res.json()
  } catch (e) {
    console.error("Failed to fetch users", e)
  }
}

const fetchLogs = async () => {
  if (activeTab.value !== 'system') return
  try {
    const res = await fetch(`${BACKEND_URL}/api/logs`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) logs.value = await res.json()
  } catch (e) {
    console.error("Failed to fetch logs", e)
  }
}

const addUser = async () => {
  if (!newUserForm.value.discord_id || !newUserForm.value.username) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/admin/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionToken.value}`
      },
      body: JSON.stringify(newUserForm.value)
    })
    if (res.ok) {
      newUserForm.value = { discord_id: '', username: '', role: 'user' }
      await fetchUsers()
      await showAlert(t('adminPanel.alerts.userAdded'), t('dashboard.successTitle'))
    } else {
      const data = await res.json()
      await showAlert(data.detail || t('adminPanel.alerts.errorAdding'), "ERROR")
    }
  } catch (e) {
    await showAlert("Network error", "ERROR")
  } finally {
    isLoading.value = false
  }
}

const updateUserRole = async (discord_id: string, newRole: string) => {
  if (!(await showConfirm(`Vuoi cambiare il ruolo a ${newRole}?`, "CONFERMA"))) return
  try {
    const res = await fetch(`${BACKEND_URL}/api/admin/users/${discord_id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionToken.value}`
      },
      body: JSON.stringify({ role: newRole })
    })
    if (res.ok) {
      await fetchUsers()
    } else {
      const data = await res.json()
      await showAlert(data.detail || t('adminPanel.alerts.errorUpdating'), "ERROR")
    }
  } catch (e) {
    console.error(e)
  }
}

const deleteUser = async (discord_id: string) => {
  if (!(await showConfirm(t('adminPanel.alerts.confirmDelete'), t('modal.systemAlert')))) return
  try {
    const res = await fetch(`${BACKEND_URL}/api/admin/users/${discord_id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      await fetchUsers()
    } else {
      const data = await res.json()
      await showAlert(data.detail || t('adminPanel.alerts.errorDeleting'), "ERROR")
    }
  } catch (e) {
    console.error(e)
  }
}

const restartSystem = async () => {
  if (!(await showConfirm(t('dashboard.restartConfirmMessage'), t('dashboard.systemRebootTitle')))) return
  
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/system/restart`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${sessionToken.value}`
      }
    })
    if (res.ok) {
      await showAlert(t('dashboard.restartSuccessMessage'), t('dashboard.rebootingTitle'))
    } else {
      await showAlert(t('dashboard.errorRestart'), "ERROR")
    }
  } catch (err: any) {
    await showAlert(err.message, "ERROR")
  } finally {
    isLoading.value = false
  }
}

const changeTab = (tab: string) => {
  activeTab.value = tab
  if (tab === 'system') {
    fetchLogs()
    if (!logsInterval) logsInterval = setInterval(fetchLogs, 2000)
  } else {
    if (logsInterval) {
      clearInterval(logsInterval)
      logsInterval = null
    }
    if (tab === 'overview') fetchStats()
    if (tab === 'users') fetchUsers()
  }
}

onMounted(() => {
  // Check if user is admin via JWT
  if (sessionToken.value) {
    try {
      const base64Url = sessionToken.value.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join('')))
      if (!payload || payload.role !== 'admin') {
        router.replace({ name: 'Dashboard' })
        return
      }
    } catch (e) {
      router.replace({ name: 'Dashboard' })
      return
    }
  } else {
    router.replace({ name: 'Login' })
    return
  }

  fetchStats()
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
    
    <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-8 border-b border-gray-800 pb-4">
      <h2 class="font-rajdhani text-2xl md:text-3xl font-bold neon-text-cyan text-center md:text-left">{{ t('adminPanel.title') }}</h2>
      <div class="flex items-center gap-4">
        <router-link to="/" class="text-sm text-cyber-cyan hover:text-white transition-colors whitespace-nowrap font-bold">
          {{ t('adminPanel.backToDashboard') }}
        </router-link>
        <button @click="logout" class="text-sm text-gray-400 hover:text-cyber-pink transition-colors whitespace-nowrap">{{ t('dashboard.logout') }}</button>
      </div>
    </div>

    <!-- TABS NAV -->
    <div class="flex flex-wrap border-b border-gray-800 mb-6">
      <button 
        @click="changeTab('overview')"
        :class="['px-6 py-3 font-rajdhani text-lg font-bold transition-colors', activeTab === 'overview' ? 'text-cyber-cyan border-b-2 border-cyber-cyan' : 'text-gray-500 hover:text-gray-300']"
      >
        OVERVIEW
      </button>
      <button 
        @click="changeTab('users')"
        :class="['px-6 py-3 font-rajdhani text-lg font-bold transition-colors', activeTab === 'users' ? 'text-cyber-cyan border-b-2 border-cyber-cyan' : 'text-gray-500 hover:text-gray-300']"
      >
        USERS
      </button>
      <button 
        @click="changeTab('system')"
        :class="['px-6 py-3 font-rajdhani text-lg font-bold transition-colors', activeTab === 'system' ? 'text-cyber-cyan border-b-2 border-cyber-cyan' : 'text-gray-500 hover:text-gray-300']"
      >
        SYSTEM
      </button>
    </div>

    <!-- OVERVIEW TAB -->
    <div v-if="activeTab === 'overview'" class="space-y-6 animate-fade-in">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-gray-900/50 border border-gray-800 p-6 rounded flex flex-col items-center justify-center">
          <span class="text-gray-400 font-rajdhani text-lg mb-2 uppercase">{{ t('adminPanel.overview.totalUsers') }}</span>
          <span class="text-4xl font-bold text-cyber-cyan">{{ stats.total_users }}</span>
        </div>
        <div class="bg-gray-900/50 border border-gray-800 p-6 rounded flex flex-col items-center justify-center">
          <span class="text-gray-400 font-rajdhani text-lg mb-2 uppercase">{{ t('adminPanel.overview.configuredGuilds') }}</span>
          <span class="text-4xl font-bold text-cyber-purple">{{ stats.total_configs }}</span>
        </div>
        <div class="bg-gray-900/50 border border-gray-800 p-6 rounded flex flex-col items-center justify-center">
          <span class="text-gray-400 font-rajdhani text-lg mb-2 uppercase">{{ t('adminPanel.overview.activeGuilds') }}</span>
          <span class="text-4xl font-bold text-cyber-green">{{ stats.active_configs }}</span>
        </div>
      </div>
    </div>

    <!-- USERS TAB -->
    <div v-if="activeTab === 'users'" class="space-y-6 animate-fade-in">
      <div class="bg-gray-900/50 border border-gray-800 p-6 rounded">
        <h3 class="font-rajdhani text-xl text-cyber-cyan mb-4">{{ t('adminPanel.users.addNewUser') }}</h3>
        <div class="grid grid-cols-1 md:grid-cols-12 gap-4">
          <input v-model="newUserForm.discord_id" type="text" :placeholder="t('adminPanel.users.discordId')" class="neon-input col-span-1 md:col-span-4 w-full">
          <input v-model="newUserForm.username" type="text" :placeholder="t('adminPanel.users.username')" class="neon-input col-span-1 md:col-span-4 w-full">
          <select v-model="newUserForm.role" class="neon-input bg-gray-900 col-span-1 md:col-span-2 w-full">
            <option value="user">{{ t('adminPanel.users.roleUser') }}</option>
            <option value="admin">{{ t('adminPanel.users.roleAdmin') }}</option>
          </select>
          <button @click="addUser" :disabled="isLoading" class="neon-btn-primary col-span-1 md:col-span-2 w-full">{{ t('adminPanel.users.add') }}</button>
        </div>
      </div>

      <div class="bg-gray-900/50 border border-gray-800 rounded overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-800/50 text-gray-400 font-rajdhani uppercase text-sm">
              <th class="p-4 border-b border-gray-800">{{ t('adminPanel.users.discordId') }}</th>
              <th class="p-4 border-b border-gray-800">{{ t('adminPanel.users.username') }}</th>
              <th class="p-4 border-b border-gray-800">{{ t('adminPanel.users.role') }}</th>
              <th class="p-4 border-b border-gray-800">{{ t('adminPanel.users.addedAt') }}</th>
              <th class="p-4 border-b border-gray-800 text-right">{{ t('adminPanel.users.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.discord_id" class="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
              <td class="p-4 font-mono text-gray-300 text-sm whitespace-nowrap">{{ u.discord_id }}</td>
              <td class="p-4 text-gray-300">{{ u.username }}</td>
              <td class="p-4">
                <span :class="u.role === 'admin' ? 'text-cyber-pink font-bold' : 'text-gray-400'">
                  {{ u.role.toUpperCase() }}
                </span>
              </td>
              <td class="p-4 text-gray-500 text-sm whitespace-nowrap">{{ new Date(u.added_at).toLocaleString() }}</td>
              <td class="p-4 text-right space-x-2 whitespace-nowrap">
                <button 
                  v-if="u.role === 'user'" 
                  @click="updateUserRole(u.discord_id, 'admin')" 
                  class="text-xs bg-gray-800 hover:bg-gray-700 text-cyber-cyan px-2 py-1 rounded transition-colors"
                >
                  Make Admin
                </button>
                <button 
                  v-if="u.role === 'admin'" 
                  @click="updateUserRole(u.discord_id, 'user')" 
                  class="text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 px-2 py-1 rounded transition-colors"
                >
                  Demote
                </button>
                <button 
                  @click="deleteUser(u.discord_id)" 
                  class="text-xs bg-red-900/40 hover:bg-red-800 text-red-200 px-2 py-1 rounded transition-colors"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SYSTEM TAB -->
    <div v-if="activeTab === 'system'" class="space-y-6 animate-fade-in">
      <div class="bg-red-900/10 border border-red-900/30 p-6 rounded flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h3 class="font-rajdhani text-xl text-red-400 mb-1">{{ t('adminPanel.system.systemRestart') }}</h3>
          <p class="text-gray-500 text-sm">{{ t('adminPanel.system.restartDesc') }}</p>
        </div>
        <button 
          @click="restartSystem" 
          :disabled="isLoading" 
          class="text-sm bg-red-900/40 hover:bg-red-800 text-red-200 border border-red-700/50 px-6 py-2 rounded transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          {{ t('dashboard.restartSystem') }}
        </button>
      </div>

      <div class="border border-gray-800 rounded bg-black/60 overflow-hidden mt-6">
        <div class="bg-gray-900/80 p-3 font-rajdhani text-cyber-cyan font-bold flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
          {{ t('adminPanel.system.liveBotLogs') }}
        </div>
        <div class="p-4 h-96 overflow-y-auto font-mono text-sm text-gray-300 space-y-1 custom-scrollbar">
          <div v-for="(log, idx) in logs" :key="idx" class="border-b border-gray-800/50 pb-1">
            <span class="text-gray-500">[{{ new Date(log.timestamp).toLocaleTimeString() }}]</span>
            <span :class="log.level === 'error' ? 'text-red-400' : 'text-cyber-green ml-2'">{{ log.message }}</span>
          </div>
          <div v-if="logs.length === 0" class="text-gray-600 italic">{{ t('dashboard.noLogsAvailable') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
