<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()

const userRole = ref<string>('user')
const guildsInfo = ref<any[]>([])
const selectedGuild = ref<string>('')
const config = ref<any>(null)
const isLoading = ref(false)
const saveSuccess = ref(false)
const saveError = ref(false)

const allLanguages = ref<any[]>([])

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
    console.error("Error decoding token", e)
  }
}

const loadLanguages = async () => {
    try {
        const res = await fetch(`${BACKEND_URL}/api/languages`, {
            headers: { 'Authorization': `Bearer ${sessionToken.value}` }
        })
        if (res.ok) {
            allLanguages.value = await res.json()
        }
    } catch (e) {
        console.error(e)
    }
}

const loadGuilds = async () => {
  if (!sessionToken.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/drops/me`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (!res.ok) throw new Error("Auth error")
    const user = await res.json()
    const gInfo = user.guilds_info || []
    
    if (userRole.value === 'admin') {
      guildsInfo.value = gInfo
    } else {
      // In a real scenario, filter for guilds where user is admin
      guildsInfo.value = gInfo
    }
    
    if (guildsInfo.value.length > 0) {
      selectedGuild.value = guildsInfo.value[0].id
      await loadConfig()
    }
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const loadConfig = async () => {
  if (!selectedGuild.value) return
  isLoading.value = true
  try {
    const res = await fetch(`${BACKEND_URL}/api/config/${selectedGuild.value}`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (res.ok) {
      config.value = await res.json()
      if (!config.value.translation_mode) config.value.translation_mode = 'channel'
      if (!config.value.translation_languages) config.value.translation_languages = []
    }
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const saveConfig = async () => {
  if (!config.value) return
  saveSuccess.value = false
  saveError.value = false
  
  try {
    const res = await fetch(`${BACKEND_URL}/api/config`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${sessionToken.value}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config.value)
    })
    
    if (res.ok) {
      saveSuccess.value = true
      setTimeout(() => { saveSuccess.value = false }, 3000)
    } else {
      saveError.value = true
    }
  } catch (e) {
    console.error(e)
    saveError.value = true
  }
}

const toggleLanguage = (code: string) => {
    const idx = config.value.translation_languages.indexOf(code)
    if (idx >= 0) {
        config.value.translation_languages.splice(idx, 1)
    } else {
        config.value.translation_languages.push(code)
    }
}

onMounted(async () => {
  if (!sessionToken.value) {
    router.replace({ name: 'Login' })
    return
  }
  await loadLanguages()
  await loadGuilds()
})

const goBack = () => {
  router.push({ name: 'Dashboard' })
}

</script>

<template>
  <div class="p-4 md:p-8 max-w-4xl mx-auto animate-fade-in">
    <div class="flex items-center gap-4 mb-8 border-b border-gray-800 pb-6">
      <button @click="goBack" class="p-2 bg-gray-900 rounded-full hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
      </button>
      <div>
        <h1 class="font-rajdhani text-3xl font-bold neon-text-purple tracking-wider uppercase">{{ t('translationAdmin.title') }}</h1>
        <p class="text-gray-500 font-mono text-sm mt-1">{{ t('translationAdmin.subtitle') }}</p>
      </div>
    </div>
    
    <div v-if="isLoading" class="text-center py-12 text-cyber-purple font-mono animate-pulse">
      {{ t('translationAdmin.loading') }}
    </div>
    
    <div v-else-if="guildsInfo.length === 0" class="glass-panel p-8 text-center text-gray-400">
      {{ t('translationAdmin.noPermissions') }}
    </div>
    
    <div v-else class="space-y-6">
      <div class="glass-panel p-6 rounded-xl">
        <label class="block text-sm font-mono text-gray-400 mb-2">{{ t('translationAdmin.selectServer') }}</label>
        <select v-model="selectedGuild" @change="loadConfig" class="w-full bg-gray-900 border border-gray-700 rounded p-3 text-white focus:border-cyber-purple focus:outline-none focus:ring-1 focus:ring-cyber-purple transition-colors">
          <option v-for="g in guildsInfo" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
      </div>
      
      <div v-if="config" class="glass-panel p-6 rounded-xl space-y-6">
        <div>
          <h3 class="font-rajdhani text-xl font-bold text-cyber-cyan mb-4">{{ t('translationAdmin.replyMode') }}</h3>
          <div class="flex flex-col gap-4">
            <label class="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" v-model="config.translation_channel" class="form-checkbox h-5 w-5 text-cyber-purple bg-gray-900 border-gray-700 rounded focus:ring-cyber-purple focus:ring-offset-gray-900">
              <span class="text-gray-300 font-mono">{{ t('translationAdmin.modeChannel') }}</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" v-model="config.translation_ephemeral" class="form-checkbox h-5 w-5 text-cyber-purple bg-gray-900 border-gray-700 rounded focus:ring-cyber-purple focus:ring-offset-gray-900">
              <span class="text-gray-300 font-mono">{{ t('translationAdmin.modeEphemeral') }}</span>
            </label>
          </div>
          <p class="text-xs text-gray-500 mt-4 font-mono leading-relaxed">
            {{ t('translationAdmin.modeDesc') }}
          </p>
        </div>
        
        <div class="border-t border-gray-800 pt-6">
          <h3 class="font-rajdhani text-xl font-bold text-cyber-cyan mb-4">{{ t('translationAdmin.availableLangs') }}</h3>
          <p class="text-sm text-gray-400 font-mono mb-4">{{ t('translationAdmin.availableLangsDesc') }}</p>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div v-for="lang in allLanguages" :key="lang.code" 
                 @click="toggleLanguage(lang.code)"
                 class="border rounded-lg p-3 cursor-pointer flex flex-col items-center gap-2 transition-colors"
                 :class="config.translation_languages.includes(lang.code) ? 'border-cyber-purple bg-cyber-purple/10' : 'border-gray-800 hover:border-gray-600 bg-gray-900/50'">
              <span class="text-3xl">{{ lang.emoji }}</span>
              <span class="text-sm font-bold text-gray-300">{{ lang.name }}</span>
            </div>
          </div>
          <div v-if="allLanguages.length === 0" class="text-yellow-500 font-mono text-sm">
            {{ t('translationAdmin.noLangsInDb') }}
          </div>
        </div>
        
        <div class="pt-6 border-t border-gray-800 flex items-center justify-between">
          <div>
            <span v-if="saveSuccess" class="text-green-500 font-mono text-sm">{{ t('translationAdmin.saveSuccess') }}</span>
            <span v-if="saveError" class="text-red-500 font-mono text-sm">{{ t('translationAdmin.saveError') }}</span>
          </div>
          <button @click="saveConfig" class="bg-cyber-purple hover:bg-cyber-purple/80 text-white font-bold py-2 px-6 rounded transition-colors shadow-[0_0_10px_rgba(188,19,254,0.4)]">
            {{ t('translationAdmin.saveBtn') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
