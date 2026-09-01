<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { t } from '../i18n'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const sessionToken = ref<string | null>(localStorage.getItem('dab_session_token'))
const router = useRouter()

const userRole = ref<string>('user')
const username = ref<string>('')
const guildsInfo = ref<any[]>([])
const isLoading = ref(false)

if (sessionToken.value) {
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
  } catch (e) {
    console.error("Error decoding token", e)
  }
}

const logout = () => {
  localStorage.removeItem('dab_session_token')
  sessionToken.value = null
  router.replace({ name: 'Login' })
}

const loadGuildsAndBuilds = async () => {
  if (!sessionToken.value) return
  isLoading.value = true
  try {
    // 1. Prendi info utente (con le gilde)
    const res = await fetch(`${BACKEND_URL}/api/drops/me`, {
      headers: { 'Authorization': `Bearer ${sessionToken.value}` }
    })
    if (!res.ok) throw new Error("Errore auth")
    const user = await res.json()
    const guilds = user.guilds || []
    const guildsInfoArray = user.guilds_info || []
    
    // 2. Per ogni gilda cerca la build dell'utente
    const info = []
    for (const g of guilds) {
      const gInfo = guildsInfoArray.find((x: any) => x.id === g)
      const name = gInfo ? gInfo.name : g
      const icon = gInfo ? gInfo.icon : null
      try {
        const bRes = await fetch(`${BACKEND_URL}/api/drops/guilds/${g}/builds`, {
          headers: { 'Authorization': `Bearer ${sessionToken.value}` }
        })
        if (bRes.ok) {
          const build = await bRes.json()
          info.push({ guildId: g, name, icon, status: build ? build.status : 'Nessuna build' })
        } else {
          info.push({ guildId: g, name, icon, status: 'Errore' })
        }
      } catch (e) {
        info.push({ guildId: g, name, icon, status: 'Errore' })
      }
    }
    guildsInfo.value = info
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  if (!sessionToken.value) {
    router.replace({ name: 'Login' })
  } else {
    loadGuildsAndBuilds()
  }
})

</script>

<template>
  <div class="p-4 md:p-8 max-w-6xl mx-auto animate-fade-in">
    <div class="flex flex-col md:flex-row justify-between items-center mb-10 border-b border-gray-800 pb-6 text-center md:text-left">
      <div>
        <h1 class="font-rajdhani text-4xl font-bold neon-text-cyan tracking-wider uppercase">{{ t('dashboard.hubTitle') }}</h1>
        <p class="text-gray-400 font-mono mt-2">{{ t('dashboard.welcomeBack') }} <span class="text-cyber-purple font-bold">{{ username }}</span></p>
      </div>
      <button @click="logout" class="mt-4 md:mt-0 text-sm text-gray-500 hover:text-cyber-pink transition-colors font-mono">
        {{ t('dashboard.logoutProtocol') }}
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
      <!-- Drops Card -->
      <router-link to="/drops" class="glass-panel p-6 rounded-xl hover:border-cyber-purple hover:shadow-[0_0_15px_rgba(188,19,254,0.3)] transition-all cursor-pointer group flex flex-col items-center text-center">
        <div class="w-16 h-16 rounded-full bg-cyber-purple/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <svg class="w-8 h-8 text-cyber-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
        </div>
        <h3 class="font-rajdhani text-xl font-bold text-gray-200 uppercase tracking-wide">{{ t('dashboard.dropsSystem') }}</h3>
        <p class="text-sm text-gray-500 font-mono mt-2">{{ t('dashboard.dropsSystemDesc') }}</p>
      </router-link>

      <!-- Broadcasting Card -->
      <router-link v-if="userRole === 'admin' || userRole === 'guild_admin'" to="/broadcasting" class="glass-panel p-6 rounded-xl hover:border-cyber-cyan hover:shadow-[0_0_15px_rgba(0,255,255,0.3)] transition-all cursor-pointer group flex flex-col items-center text-center">
        <div class="w-16 h-16 rounded-full bg-cyber-cyan/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <svg class="w-8 h-8 text-cyber-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"></path></svg>
        </div>
        <h3 class="font-rajdhani text-xl font-bold text-gray-200 uppercase tracking-wide">{{ t('dashboard.broadcasting') }}</h3>
        <p class="text-sm text-gray-500 font-mono mt-2">{{ t('dashboard.broadcastingDesc') }}</p>
      </router-link>

      <!-- Music Card -->
      <router-link v-if="userRole === 'admin' || userRole === 'guild_admin'" to="/music" class="glass-panel p-6 rounded-xl hover:border-cyber-pink hover:shadow-[0_0_15px_rgba(255,0,128,0.3)] transition-all cursor-pointer group flex flex-col items-center text-center">
        <div class="w-16 h-16 rounded-full bg-cyber-pink/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <svg class="w-8 h-8 text-cyber-pink" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
        </div>
        <h3 class="font-rajdhani text-xl font-bold text-gray-200 uppercase tracking-wide">{{ t('dashboard.musicPlayer') }}</h3>
        <p class="text-sm text-gray-500 font-mono mt-2">{{ t('dashboard.musicPlayerDesc') }}</p>
      </router-link>

      <!-- Drops Management Card -->
      <router-link v-if="userRole === 'admin' || userRole === 'guild_admin'" to="/drops-admin" class="glass-panel p-6 rounded-xl hover:border-yellow-500 hover:shadow-[0_0_15px_rgba(234,179,8,0.3)] transition-all cursor-pointer group flex flex-col items-center text-center">
        <div class="w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <svg class="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <h3 class="font-rajdhani text-xl font-bold text-gray-200 uppercase tracking-wide">{{ t('dashboard.dropManagement') }}</h3>
        <p class="text-sm text-gray-500 font-mono mt-2">{{ t('dashboard.dropManagementDesc') }}</p>
      </router-link>

      <!-- Admin Card -->
      <router-link v-if="userRole === 'admin'" to="/admin" class="glass-panel p-6 rounded-xl hover:border-red-500 hover:shadow-[0_0_15px_rgba(255,0,0,0.3)] transition-all cursor-pointer group flex flex-col items-center text-center">
        <div class="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
        </div>
        <h3 class="font-rajdhani text-xl font-bold text-gray-200 uppercase tracking-wide">{{ t('dashboard.adminPanelTitle') }}</h3>
        <p class="text-sm text-gray-500 font-mono mt-2">{{ t('dashboard.adminPanelDesc') }}</p>
      </router-link>
      
      <!-- Translation Admin Card -->
      <router-link v-if="userRole === 'admin' || userRole === 'guild_admin'" to="/translation-admin" class="glass-panel p-6 rounded-xl hover:border-green-500 hover:shadow-[0_0_15px_rgba(34,197,94,0.3)] transition-all cursor-pointer group flex flex-col items-center text-center">
        <div class="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
          <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path></svg>
        </div>
        <h3 class="font-rajdhani text-xl font-bold text-gray-200 uppercase tracking-wide">{{ t('dashboard.translationAdminTitle') }}</h3>
        <p class="text-sm text-gray-500 font-mono mt-2">{{ t('dashboard.translationAdminDesc') }}</p>
      </router-link>
    </div>

    <!-- My Guilds Section -->
    <div class="glass-panel p-4 md:p-8 rounded-xl">
      <h3 class="font-rajdhani text-2xl font-bold text-cyber-cyan mb-6 flex items-center gap-3">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
        {{ t('dashboard.yourGuilds') }}
      </h3>
      
      <div v-if="isLoading" class="text-center py-8 text-cyber-purple font-mono animate-pulse">
        {{ t('dashboard.scanningDb') }}
      </div>
      
      <div v-else-if="guildsInfo.length === 0" class="text-center py-8 text-gray-500 font-mono">
        {{ t('dashboard.noSyncedGuilds') }}
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="g in guildsInfo" :key="g.guildId" class="bg-gray-900/60 border border-gray-800 rounded p-4 flex justify-between items-center hover:bg-gray-800/60 transition-colors">
          <div class="flex items-center gap-3">
            <img v-if="g.icon" :src="`https://cdn.discordapp.com/icons/${g.guildId}/${g.icon}.png`" class="w-10 h-10 rounded-full border border-gray-700">
            <div v-else class="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center border border-gray-700">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
            </div>
            <div>
              <p class="font-bold text-white text-base sm:text-lg truncate max-w-[150px] sm:max-w-xs" :title="g.name">{{ g.name }}</p>
              <p class="font-mono text-gray-500 text-xs">{{ t('dashboard.guildIdLabel2') }} {{ g.guildId }}</p>
            </div>
          </div>
          <div class="flex flex-col items-start sm:items-end w-full sm:w-auto mt-3 sm:mt-0 pt-3 sm:pt-0 border-t border-gray-800 sm:border-0">
            <span class="text-xs text-gray-500 mb-1 uppercase tracking-wider">{{ t('dashboard.buildStatus') }}</span>
            <span class="px-3 py-1 rounded font-bold text-xs uppercase" 
              :class="{
                'bg-gray-700 text-gray-300': g.status === 'Nessuna build' || g.status === 'draft' || g.status === 'No build' || g.status === 'Sin build' || g.status === 'Pas de build' || g.status === 'Kein Build',
                'bg-yellow-900 text-yellow-300': g.status === 'pending',
                'bg-green-900 text-green-300': g.status === 'primary',
                'bg-red-900 text-red-300': g.status === 'Errore' || g.status === 'Error' || g.status === 'Erreur' || g.status === 'Fehler'
              }">
              <template v-if="g.status === 'Nessuna build' || g.status === 'No build' || g.status === 'Sin build' || g.status === 'Pas de build' || g.status === 'Kein Build'">{{ t('drops.statusNoBuild') }}</template>
              <template v-else-if="g.status === 'Errore' || g.status === 'Error' || g.status === 'Erreur' || g.status === 'Fehler'">{{ t('drops.statusError') }}</template>
              <template v-else>{{ g.status }}</template>
            </span>
          </div>
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
