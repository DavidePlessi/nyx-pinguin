<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { t } from '../i18n'

const router = useRouter()
const route = useRoute()

const printManual = () => {
  window.print()
}

const goBack = () => {
  router.push({ name: 'Dashboard', query: route.query })
}
</script>

<template>
  <div class="glass-panel p-4 md:p-8 printable-area bg-gray-900 text-gray-200">
    <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-8 border-b border-gray-800 pb-4 no-print">
      <h2 class="font-rajdhani text-2xl md:text-3xl font-bold neon-text-cyan text-center md:text-left">{{ t('manual.manualTitle') }}</h2>
      <div class="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
        <button @click="printManual" class="neon-btn-primary px-4 py-2 text-sm flex items-center justify-center gap-2 w-full sm:w-auto">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
          {{ t('manual.print') }}
        </button>
        <button @click="goBack" class="text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white px-4 py-2 rounded transition-colors w-full sm:w-auto border border-gray-700">
          {{ t('manual.close') }}
        </button>
      </div>
    </div>

    <div class="print-header hidden mb-8 text-center text-black">
      <h1 class="text-3xl font-bold uppercase mb-2">Nyx Pinguin</h1>
      <h2 class="text-xl">{{ t('manual.manualTitle') }}</h2>
    </div>

    <div class="space-y-8 manual-content text-lg">
      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">{{ t('manual.section1.title') }}</h3>
        <p class="mb-4">{{ t('manual.section1.p1') }}</p>
        <div class="bg-black/50 p-4 rounded border border-gray-700 no-print-bg space-y-4">
          <div>
            <span class="font-bold text-cyber-cyan">{{ t('manual.section1.listener') }}</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535787643546108004&permissions=305138688&integration_type=0&scope=applications.commands+bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">{{ t('manual.section1.invite') }} Listener</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">{{ t('manual.section1.speaker') }} 1:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535797082076479488&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">{{ t('manual.section1.invite') }} Speaker 1</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">{{ t('manual.section1.speaker') }} 2:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535976933546917898&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">{{ t('manual.section1.invite') }} Speaker 2</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">{{ t('manual.section1.speaker') }} 3:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535977660558086204&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">{{ t('manual.section1.invite') }} Speaker 3</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">{{ t('manual.section1.speaker') }} 4:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1536018514379411457&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">{{ t('manual.section1.invite') }} Speaker 4</a>
          </div>
        </div>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">{{ t('manual.section2.title') }}</h3>
        <p class="mb-4">{{ t('manual.section2.p1') }}</p>
        <ol class="list-decimal pl-6 space-y-2">
          <li v-html="t('manual.section2.li1')"></li>
          <li v-html="t('manual.section2.li2')"></li>
          <li v-html="t('manual.section2.li3')"></li>
          <li v-html="t('manual.section2.li4')"></li>
          <li v-html="t('manual.section2.li5')"></li>
        </ol>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">{{ t('manual.section3.title') }}</h3>
        <p class="mb-4" v-html="t('manual.section3.p1')"></p>
        <ol class="list-decimal pl-6 space-y-2">
          <li v-html="t('manual.section3.li1')"></li>
          <li v-html="t('manual.section3.li2')"></li>
          <li v-html="t('manual.section3.li3')"></li>
          <li v-html="t('manual.section3.li4')"></li>
        </ol>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">{{ t('manual.section4.title') }}</h3>
        <ul class="space-y-4">
          <li>
            <strong class="text-cyber-cyan">Guild ID (Server) & SCAN:</strong> {{ t('manual.section4.guildId') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">Source Channel ID:</strong> {{ t('manual.section4.sourceChannelId') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">Authorized Role ID (Opzionale):</strong> {{ t('manual.section4.authorizedRoleId') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">Destination Channels:</strong> {{ t('manual.section4.destChannels') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">External Channels (Cross-Server Broadcast):</strong> {{ t('manual.section4.externalChannels') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">Abilita Broadcasting:</strong> {{ t('manual.section4.enableBroadcasting') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">SAVE TO MAINFRAME:</strong> {{ t('manual.section4.saveToMainframe') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">BOT LOGS TERMINAL:</strong> {{ t('manual.section4.botLogsTerminal') }}
          </li>
          <li>
            <strong class="text-cyber-cyan">RESTART SYSTEM:</strong> {{ t('manual.section4.restartSystem') }}
          </li>
        </ul>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">{{ t('manual.section5.title') }}</h3>
        <p class="mb-4">{{ t('manual.section5.p1') }}</p>
        <ul class="space-y-4">
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            <strong class="text-cyber-cyan font-mono text-xl">/pinguin_on_duty</strong>
            <p class="mt-2">{{ t('manual.section5.cmdOnDuty') }}</p>
          </li>
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            <strong class="text-cyber-cyan font-mono text-xl">/pinguin_at_ease</strong>
            <p class="mt-2">{{ t('manual.section5.cmdAtEase') }}</p>
          </li>
        </ul>
      </section>

      <hr class="my-8 border-gray-800 no-print" />

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4 flex items-center gap-2">
          <svg class="w-6 h-6 text-cyber-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"></path></svg>
          {{ t('manual.sectionAdmin.title') }}
        </h3>
        <p class="mb-4">{{ t('manual.sectionAdmin.p1') }}</p>
        <ul class="space-y-4">
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            {{ t('manual.sectionAdmin.overview') }}
          </li>
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            {{ t('manual.sectionAdmin.users') }}
          </li>
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            {{ t('manual.sectionAdmin.system') }}
          </li>
        </ul>
      </section>

    </div>
  </div>
</template>

<style scoped>
@media print {
  /* Stile ottimizzato per la stampa */
  @page {
    margin: 2cm;
  }
  .printable-area {
    background-color: white !important;
    color: black !important;
    box-shadow: none !important;
    border: none !important;
  }
  .print-header {
    display: block !important;
  }
  .no-print {
    display: none !important;
  }
  .text-cyber-purple {
    color: #4a0072 !important; /* Colore più scuro per stampa */
  }
  .text-cyber-cyan {
    color: #005f73 !important; /* Colore più scuro per stampa */
  }
  a {
    color: #0000ff !important;
    text-decoration: underline !important;
  }
  .no-print-bg {
    background-color: transparent !important;
    border: 1px solid #ccc !important;
  }
}
</style>
