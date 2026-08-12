<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'

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
  <div class="glass-panel p-8 printable-area bg-gray-900 text-gray-200">
    <div class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4 no-print">
      <h2 class="font-rajdhani text-3xl font-bold neon-text-cyan">MANUALE OPERATIVO</h2>
      <div class="flex gap-4">
        <button @click="printManual" class="neon-btn-primary px-4 py-2 text-sm flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
          STAMPA
        </button>
        <button @click="goBack" class="text-sm text-gray-400 hover:text-cyber-pink transition-colors">
          Chiudi [x]
        </button>
      </div>
    </div>

    <div class="print-header hidden mb-8 text-center text-black">
      <h1 class="text-3xl font-bold uppercase mb-2">Nyx Pinguin</h1>
      <h2 class="text-xl">Manuale Operativo</h2>
    </div>

    <div class="space-y-8 manual-content text-lg">
      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">1. Come invitare i Bot</h3>
        <p class="mb-4">Per far funzionare il sistema di broadcasting, è necessario invitare sia il bot "Listener" (che ascolta l'audio) sia i bot "Speaker" (che riproducono l'audio nei canali di destinazione).</p>
        <div class="bg-black/50 p-4 rounded border border-gray-700 no-print-bg space-y-4">
          <div>
            <span class="font-bold text-cyber-cyan">Listener:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535787643546108004&permissions=305138688&integration_type=0&scope=applications.commands+bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">Invita Listener</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">Speaker 1:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535797082076479488&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">Invita Speaker 1</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">Speaker 2:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535976933546917898&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">Invita Speaker 2</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">Speaker 3:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1535977660558086204&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">Invita Speaker 3</a>
          </div>
          <div>
            <span class="font-bold text-cyber-cyan">Speaker 4:</span><br/>
            <a href="https://discord.com/oauth2/authorize?client_id=1536018514379411457&permissions=36701184&integration_type=0&scope=bot" target="_blank" class="text-sm text-blue-400 hover:underline break-all">Invita Speaker 4</a>
          </div>
        </div>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">2. Come recuperare il Guild ID (ID del Server)</h3>
        <p class="mb-4">Per configurare il sistema, ti servirà l'ID del server Discord (Guild ID).</p>
        <ol class="list-decimal pl-6 space-y-2">
          <li>Apri le <strong>Impostazioni Utente</strong> di Discord (l'icona a forma di ingranaggio in basso a sinistra).</li>
          <li>Vai su <strong>Avanzate</strong> (sotto la sezione Impostazioni App).</li>
          <li>Attiva l'opzione <strong>Modalità Sviluppatore</strong>.</li>
          <li>Torna alla lista dei server, fai clic destro sull'icona del tuo server e seleziona <strong>Copia ID server</strong> (o Copia ID).</li>
          <li>Incolla questo ID nel campo "Guild ID (Server)" dell'interfaccia web e clicca su SCAN.</li>
        </ol>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">3. Come recuperare il Channel ID (ID del Canale)</h3>
        <p class="mb-4">Per inviare l'audio in canali di <strong>altri server</strong>, ti servirà l'ID di quel canale vocale (Channel ID).</p>
        <ol class="list-decimal pl-6 space-y-2">
          <li>Assicurati di aver attivato la <strong>Modalità Sviluppatore</strong> come spiegato nel punto precedente.</li>
          <li>Entra nel server esterno dove vuoi trasmettere.</li>
          <li>Fai clic destro sul nome del canale vocale desiderato e seleziona <strong>Copia ID canale</strong> (o Copia ID).</li>
          <li>Incolla l'ID appena copiato nel campo "External Channels (ID)" della Dashboard.</li>
        </ol>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">4. Funzioni dell'Interfaccia</h3>
        <ul class="space-y-4">
          <li>
            <strong class="text-cyber-cyan">Guild ID (Server) & SCAN:</strong> Inserisci l'ID del server e clicca su SCAN per caricare tutti i canali vocali e i ruoli presenti nel server.
          </li>
          <li>
            <strong class="text-cyber-cyan">Source Channel ID:</strong> Seleziona il canale vocale "sorgente". Il bot Listener si connetterà qui per catturare l'audio di chi parla.
          </li>
          <li>
            <strong class="text-cyber-cyan">Authorized Role ID (Opzionale):</strong> Seleziona un ruolo. Solo gli utenti in possesso di questo ruolo verranno trasmessi. Se lasciato vuoto, l'audio di chiunque nel canale sorgente verrà catturato.
          </li>
          <li>
            <strong class="text-cyber-cyan">Destination Channels:</strong> Seleziona uno o più canali di destinazione all'interno del server corrente. I bot Speaker si connetteranno a questi canali e trasmetteranno l'audio catturato dal Listener.
          </li>
          <li>
            <strong class="text-cyber-cyan">External Channels (Cross-Server Broadcast):</strong> Se vuoi trasmettere l'audio anche in altri server, puoi incollare in questo campo di testo gli ID dei canali vocali esterni (separati da a capo o virgola). Assicurati che i bot "Speaker" siano stati invitati in quei server!
          </li>
          <li>
            <strong class="text-cyber-cyan">Abilita Broadcasting:</strong> Interruttore principale per attivare o disattivare l'intero sistema di broadcasting per il server specificato.
          </li>
          <li>
            <strong class="text-cyber-cyan">SAVE TO MAINFRAME:</strong> Salva la configurazione attuale nel database. Le modifiche verranno ricaricate dal sistema.
          </li>
          <li>
            <strong class="text-cyber-cyan">BOT LOGS TERMINAL:</strong> Un terminale integrato per visualizzare i log del sistema in tempo reale. Utile per monitorare lo stato di connessione e capire se ci sono errori.
          </li>
          <li>
            <strong class="text-cyber-cyan">RESTART SYSTEM:</strong> Riavvia forzatamente i bot. Usalo se il sistema sembra bloccato o se i bot non si connettono ai canali (causerà una breve interruzione del servizio).
          </li>
        </ul>
      </section>

      <section>
        <h3 class="text-2xl font-bold text-cyber-purple mb-4">5. Comandi Discord (Slash Commands)</h3>
        <p class="mb-4">Una volta configurato e attivato il sistema tramite questa interfaccia, puoi controllare la trasmissione direttamente da Discord:</p>
        <ul class="space-y-4">
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            <strong class="text-cyber-cyan font-mono text-xl">/pinguin_on_duty</strong>
            <p class="mt-2">Avvia il broadcasting audio. Il bot Listener entrerà nel canale sorgente e i bot Speaker si collegheranno ai canali di destinazione configurati.</p>
          </li>
          <li class="bg-black/20 p-4 rounded border border-gray-800">
            <strong class="text-cyber-cyan font-mono text-xl">/pinguin_at_ease</strong>
            <p class="mt-2">Ferma immediatamente la trasmissione. Tutti i bot si disconnetteranno dai rispettivi canali vocali.</p>
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
