<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''
const router = useRouter()
const route = useRoute()
const isChecking = ref(true)

const loginWithDiscord = () => {
  const currentGuild = route.query.guild || route.query.id
  let url = `${BACKEND_URL}/api/oauth/login`
  if (currentGuild) {
    url += `?state=${currentGuild}`
  }
  window.location.href = url
}

onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search)
  const token = urlParams.get('token')
  
  if (token) {
    localStorage.setItem('dab_session_token', token)
    // Rimuoviamo il token dai query params prima di navigare
    const newQuery = { ...route.query }
    delete newQuery.token
    
    router.replace({ name: 'Dashboard', query: newQuery })
  } else {
    isChecking.value = false
  }
})
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[50vh]">
    <div v-if="isChecking" class="text-cyber-cyan font-mono animate-pulse">
      Verifica credenziali in corso...
    </div>
    <div v-else class="glass-panel p-10 text-center max-w-md w-full">
      <h2 class="font-orbitron text-2xl mb-6 text-gray-300">ADMIN ACCESS REQUIRED</h2>
      <button @click="loginWithDiscord" class="neon-btn-primary w-full flex items-center justify-center gap-3">
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"/></svg>
        AUTHENTICATE
      </button>
    </div>
  </div>
</template>
