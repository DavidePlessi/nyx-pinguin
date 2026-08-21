<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CyberModal from '../components/CyberModal.vue'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()
const route = useRoute()

const userRole = ref<string>('user')

if (sessionToken.value) {
  try {
    const base64Url = sessionToken.value.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    const payload = JSON.parse(jsonPayload)
    if (payload && payload.role) {
      userRole.value = payload.role
    }
  } catch (e) {
    console.error("Error decoding token", e)
  }
}

const isLoading = ref(false)
const error = ref('')

const guildId = ref('')
const sourceChannelId = ref('')
const sourceRoleId = ref('')
const destChannels = ref<string[]>([])
const externalDestChannelsText = ref('')
const isActive = ref(false)

const availableChannels = ref<any[]>([])
const availableRoles = ref<any[]>([])

const modalState = ref({
  show: false,
  title: 'SYSTEM ALERT',
  message: '',
  isConfirm: false,
  resolve: null as ((value: boolean) => void) | null
})

const showAlert = (message: string, title?: string) => {
  return new Promise<boolean>((resolve) => {
    modalState.value = { show: true, title: title || t('modal.systemAlert'), message, isConfirm: false, resolve }
  })
}

// const showConfirm = (message: string, title?: string) => {
//   return new Promise<boolean>((resolve) => {
//     modalState.value = { show: true, title: title || t('modal.systemAlert'), message, isConfirm: true, resolve }
//   })
// }

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
      throw new Error(t('dashboard.errorLoading'))
    }
    const data = await res.json()
    sourceChannelId.value = data.source_channel_id || ''
    sourceRoleId.value = data.source_role_id || ''
    destChannels.value = data.dest_channels || []
    externalDestChannelsText.value = (data.external_dest_channels || []).join('\n')
    isActive.value = data.is_active || false

    await fetchDiscordData()
  } catch (err: any) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const saveConfig = async () => {
  if (!guildId.value || !sourceChannelId.value) {
    error.value = t('dashboard.errorRequiredFields')
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  const extList = externalDestChannelsText.value.split(/[\n,]+/).map(s => s.trim()).filter(s => s)

  const payload = {
    guild_id: guildId.value,
    source_channel_id: sourceChannelId.value,
    source_role_id: sourceRoleId.value || null,
    dest_channels: destChannels.value,
    external_dest_channels: extList,
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
      throw new Error(t('dashboard.errorSaving'))
    }
    await showAlert(t('dashboard.successSaveMessage'), t('dashboard.successTitle'))
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
      <h2 class="font-rajdhani text-2xl md:text-3xl font-bold neon-text-cyan text-center md:text-left">{{ t('dashboard.matrixConfiguration') }}</h2>
      <div class="flex items-center gap-4">
        <router-link to="/" class="text-sm text-cyber-cyan hover:text-white transition-colors whitespace-nowrap font-bold flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
          BACK TO HUB
        </router-link>
      </div>
    </div>

    <div v-if="error" class="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-md mb-6 font-mono">
      {{ t('dashboard.errorPrefix') }} {{ error }}
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      
      <!-- Target Selection -->
      <div class="space-y-6">
        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">{{ t('dashboard.guildIdLabel') }}</label>
          <div class="flex gap-2">
            <input v-model="guildId" type="text" class="neon-input flex-1" :placeholder="t('dashboard.guildIdPlaceholder')">
            <button @click="loadConfig" :disabled="isLoading" class="bg-gray-800 hover:bg-gray-700 px-4 rounded border border-gray-600 transition-colors">
              {{ t('dashboard.scan') }}
            </button>
          </div>
        </div>

        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">{{ t('dashboard.sourceChannelIdLabel') }}</label>
          <select v-model="sourceChannelId" class="neon-input bg-gray-900">
            <option value="">{{ t('dashboard.selectChannel') }}</option>
            <option v-for="ch in availableChannels" :key="ch.id" :value="ch.id">
              {{ ch.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">{{ t('dashboard.authorizedRoleIdLabel') }}</label>
          <select v-model="sourceRoleId" class="neon-input bg-gray-900 border-cyber-purple/50 focus:border-cyber-purple">
            <option value="">{{ t('dashboard.leaveEmptyForAll') }}</option>
            <option v-for="r in availableRoles" :key="r.id" :value="r.id">
              {{ r.name }}
            </option>
          </select>
          <p class="text-xs text-gray-500 mt-1 font-mono">{{ t('dashboard.roleHint') }}</p>
        </div>
      </div>

      <!-- Destinations -->
      <div class="space-y-6">
        <div>
          <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">{{ t('dashboard.destChannelsLabel') }}</label>
          <div class="h-48 overflow-y-auto border border-gray-800 rounded bg-gray-900/50 p-2 space-y-2 custom-scrollbar">
            <label v-for="ch in availableChannels" :key="ch.id" class="flex items-center gap-2 p-2 hover:bg-gray-800 rounded cursor-pointer">
              <input type="checkbox" :value="ch.id" v-model="destChannels" class="accent-cyber-cyan w-4 h-4">
              <span class="text-gray-300 font-mono text-sm">{{ ch.name }}</span>
            </label>
            <div v-if="availableChannels.length === 0" class="text-gray-500 text-sm text-center py-10">
              {{ t('dashboard.runScanHint') }}
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-1 font-mono">{{ t('dashboard.destChannelsHint') }}</p>
        </div>


        <div class="flex items-center gap-3 pt-2">
          <input v-model="isActive" type="checkbox" id="isActive" class="w-5 h-5 accent-cyber-cyan bg-gray-900 border-gray-700 rounded">
          <label for="isActive" class="font-rajdhani text-lg text-gray-300">{{ t('dashboard.enableBroadcasting') }}</label>
        </div>
      </div>

    </div>

    <!-- External Destinations (Full Width) -->
    <div class="mt-8">
      <label class="block font-rajdhani text-gray-400 mb-2 uppercase tracking-wide">{{ t('dashboard.externalChannelsLabel') }}</label>
      <textarea v-model="externalDestChannelsText" rows="3" class="neon-input bg-gray-900 w-full" :placeholder="t('dashboard.externalChannelsPlaceholder')"></textarea>
      <p class="text-xs text-gray-500 mt-1 font-mono">{{ t('dashboard.externalChannelsHint') }}</p>
    </div>

    <div class="mt-10 pt-6 border-t border-gray-800 flex justify-end">
      <button @click="saveConfig" :disabled="isLoading" class="neon-btn-primary w-full md:w-auto px-12">
        {{ isLoading ? t('dashboard.uploading') : t('dashboard.saveToMainframe') }}
      </button>
    </div>
    
  </div>
</template>
