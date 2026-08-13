import { Client, GatewayIntentBits, REST, Routes, SlashCommandBuilder } from 'discord.js';
import { joinVoiceChannel, createAudioPlayer, createAudioResource, StreamType, VoiceConnectionStatus, EndBehaviorType, getVoiceConnection, NoSubscriberBehavior } from '@discordjs/voice';
import { MongoClient } from 'mongodb';
import { config } from 'dotenv';
import { resolve } from 'path';
import { existsSync } from 'fs';
import { Player, onBeforeCreateStream, Track, SearchResult, Playlist } from 'discord-player';
import { DefaultExtractors } from '@discord-player/extractor';
import { YoutubeiExtractor } from 'discord-player-youtubei';
import yt from 'youtube-dl-exec';

// Load .env from backend
config({ path: resolve('../.env') });

const MONGO_URI = process.env.MONGO_URI;
const DB_NAME = process.env.MONGO_DB_NAME;
const PRIMARY_TOKEN = process.env.DISCORD_PRIMARY_TOKEN;
const AUX_TOKENS = (process.env.DISCORD_AUX_TOKENS || '').split(',').map(t => t.trim()).filter(t => t);
const CLIENT_ID = process.env.DISCORD_CLIENT_ID;
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

// Clients
const primaryBot = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMessages, GatewayIntentBits.GuildMembers] });
const auxBots = AUX_TOKENS.map(() => new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates] }));

const musicPlayers = new Map(); // botId -> Player

let dbClient;
let audioPlayer = createAudioPlayer({
    behaviors: {
        noSubscriber: NoSubscriberBehavior.Play,
        maxMissedFrames: Math.round(5000 / 20)
    }
});

const activeBroadcasts = new Map(); // Traccia: sourceGuildId -> [{botId, targetGuildId}]

// Registra i comandi Slash
async function registerCommands() {
    const commands = [
        new SlashCommandBuilder().setName('pinguin_on_duty').setDescription('Avvia il broadcasting audio dai canali configurati'),
        new SlashCommandBuilder().setName('pinguin_at_ease').setDescription('Ferma il broadcasting audio'),
        new SlashCommandBuilder().setName('pinguin_dashboard').setDescription('Ottieni il link alla Dashboard Web per questo server'),
        new SlashCommandBuilder()
            .setName('pinguin_play')
            .setDescription('Riproduce musica o aggiunge alla fine della coda')
            .addStringOption(option => option.setName('query').setDescription('Link o titolo del brano/playlist').setRequired(true)),
        new SlashCommandBuilder()
            .setName('pinguin_insert')
            .setDescription('Inserisce un brano o playlist in cima alla coda (salta la fila)')
            .addStringOption(option => option.setName('query').setDescription('Link o titolo del brano/playlist').setRequired(true)),
        new SlashCommandBuilder().setName('pinguin_queue').setDescription('Mostra la coda attuale'),
        new SlashCommandBuilder().setName('pinguin_skip').setDescription('Salta alla traccia successiva'),
        new SlashCommandBuilder().setName('pinguin_previous').setDescription('Torna alla traccia precedente'),
        new SlashCommandBuilder().setName('pinguin_pause').setDescription('Mette in pausa la musica'),
        new SlashCommandBuilder().setName('pinguin_resume').setDescription('Riprende la musica in pausa'),
        new SlashCommandBuilder().setName('pinguin_stop').setDescription('Ferma la musica e svuota la coda')
    ].map(c => c.toJSON());

    const rest = new REST({ version: '10' }).setToken(PRIMARY_TOKEN);
    try {
        console.log('Refreshing global slash commands...');
        await rest.put(Routes.applicationCommands(CLIENT_ID), { body: commands });
        console.log('✅ Slash commands registered.');
    } catch (error) {
        console.error('Error registering commands:', error);
    }
}

async function publishMessage(channel, message) {
    const db = dbClient.db(DB_NAME);
    await db.collection('ipc_messages').insertOne({ channel, data: message });
}

primaryBot.on('interactionCreate', async interaction => {
    if (!interaction.isChatInputCommand()) return;

    if (interaction.commandName === 'pinguin_on_duty') {
        await interaction.deferReply();
        const db = dbClient.db(DB_NAME);
        const config = await db.collection('guild_configs').findOne({ guild_id: interaction.guildId });
        
        if (!config || !config.is_active || !config.source_channel_id) {
            await interaction.followUp("❌ Nessuna configurazione attiva per questo server. Configuralo prima dalla Dashboard Web.");
            return;
        }

        await publishMessage("dab_updates", {
            action: "start_broadcast",
            guild_id: interaction.guildId,
            source_channel_id: config.source_channel_id,
            dest_channels: config.dest_channels,
            external_dest_channels: config.external_dest_channels,
            source_role_id: config.source_role_id
        });
        await interaction.followUp(`🐧 **Pinguin on Duty!** Avvio del broadcasting dal canale <#${config.source_channel_id}> verso ${config.dest_channels.length + (config.external_dest_channels?.length || 0)} canali...`);
    }

    if (interaction.commandName === 'pinguin_at_ease') {
        await publishMessage("dab_updates", {
            action: "stop_broadcast",
            guild_id: interaction.guildId
        });
        await interaction.reply("💤 **Pinguin at Ease.** Broadcasting fermato!");
    }

    if (interaction.commandName === 'pinguin_dashboard') {
        const url = `${FRONTEND_URL}/music?guild=${interaction.guildId}`;
        await interaction.reply({ content: `🔗 **Dashboard Musicale:** [Clicca qui per accedere](${url})`, ephemeral: true });
        return;
    }

    if (interaction.commandName.startsWith('pinguin_') && !['pinguin_on_duty', 'pinguin_at_ease', 'pinguin_dashboard'].includes(interaction.commandName)) {
        await handleMusicCommand(interaction);
    }
});

async function handleMusicCommand(interaction) {
    await interaction.deferReply();
    const userVoiceChannel = interaction.member.voice.channel;
    if (!userVoiceChannel) {
        return interaction.followUp("❌ Devi essere in un canale vocale per usare questo comando!");
    }

    let selectedBot = null;
    let selectedPlayer = null;

    // 1. Cerca bot già connesso a questo canale vocale
    for (const bot of auxBots) {
        const p = musicPlayers.get(bot.user.id);
        const queue = p?.nodes.get(interaction.guildId);
        if (queue && queue.channel.id === userVoiceChannel.id) {
            selectedBot = bot;
            selectedPlayer = p;
            break;
        }
    }

    // 2. Cerca un bot libero (priorità ai secondari)
    if (!selectedBot) {
        for (const bot of auxBots) {
            const p = musicPlayers.get(bot.user.id);
            const queue = p?.nodes.get(interaction.guildId);
            const nativeConnection = getVoiceConnection(interaction.guildId, bot.user.id);
            
            if (!queue && !nativeConnection) {
                selectedBot = bot;
                selectedPlayer = p;
                break;
            }
        }
    }

    if (!selectedBot) return interaction.followUp("❌ Tutti i pinguini sono occupati in questo momento!");

    const command = interaction.commandName;
    const query = interaction.options?.getString('query');
    const permissions = userVoiceChannel.permissionsFor(selectedBot.user);
    
    if (!permissions.has('Connect') || !permissions.has('Speak')) {
        return interaction.followUp(`❌ Il pinguino <@${selectedBot.user.id}> non ha i permessi per il tuo canale.`);
    }

    try {
        if (command === 'pinguin_play' || command === 'pinguin_insert') {
            const insert = command === 'pinguin_insert';
            
            // Fix per i link di YouTube Music
            let safeQuery = query;
            if (safeQuery.includes('music.youtube.com')) {
                safeQuery = safeQuery.replace('music.youtube.com', 'www.youtube.com');
            }

            const searchResult = await searchWithFallback(selectedPlayer, safeQuery, interaction.user);
            if (!searchResult.hasTracks()) {
                return interaction.followUp("❌ Nessun brano trovato con questa ricerca.");
            }

            const botVoiceChannel = selectedBot.guilds.cache.get(interaction.guildId)?.channels.cache.get(userVoiceChannel.id);
            if (!botVoiceChannel) {
                return interaction.followUp("❌ Il pinguino non riesce a trovare il tuo canale vocale.");
            }

            const { track } = await selectedPlayer.play(botVoiceChannel, searchResult, {
                nodeOptions: { metadata: interaction.channel },
                requestedBy: interaction.user
            });
            
            let queue = selectedPlayer.nodes.get(interaction.guildId);
            if (insert && queue && queue.tracks.size > 1) {
                 if (searchResult.playlist) {
                     const addedTracks = queue.tracks.toArray().slice(-searchResult.tracks.length);
                     addedTracks.forEach(t => queue.removeTrack(t));
                     addedTracks.reverse().forEach(t => queue.insertTrack(t, 0));
                 } else {
                     queue.removeTrack(track);
                     queue.insertTrack(track, 0);
                 }
            }
            
            return interaction.followUp(`🎶 **${insert ? 'Inserito in cima' : 'Aggiunto alla coda'}:** \`${track.title}\` tramite <@${selectedBot.user.id}>`);
        }
        
        const queue = selectedPlayer.nodes.get(interaction.guildId);
        if (!queue) return interaction.followUp("❌ Non c'è musica in riproduzione in questo canale.");

        if (command === 'pinguin_queue') {
            const currentTrack = queue.currentTrack;
            const tracks = queue.tracks.toArray().slice(0, 10).map((t, i) => `${i + 1}. **${t.title}**`);
            return interaction.followUp(`**In riproduzione:** \`${currentTrack?.title}\`\n\n**Coda:**\n${tracks.length > 0 ? tracks.join('\n') : 'Vuota'}`);
        } else if (command === 'pinguin_skip') {
            console.log(`[MUSIC COMMAND] pinguin_skip called by ${interaction.user.tag} in guild ${interaction.guildId}`);
            queue.node.skip();
            return interaction.followUp("⏩ Brano saltato.");
        } else if (command === 'pinguin_previous') {
            if (queue.history.tracks.size === 0) return interaction.followUp("❌ Nessun brano precedente.");
            queue.history.previous();
            return interaction.followUp("⏮️ Torno al brano precedente.");
        } else if (command === 'pinguin_pause') {
            queue.node.pause();
            return interaction.followUp("⏸️ Musica in pausa.");
        } else if (command === 'pinguin_resume') {
            queue.node.resume();
            return interaction.followUp("▶️ Musica ripresa.");
        } else if (command === 'pinguin_stop') {
            queue.delete();
            return interaction.followUp("⏹️ Musica fermata e pinguino cacciato.");
        }
    } catch (e) {
        console.error(e);
        return interaction.followUp("❌ Si è verificato un errore durante l'esecuzione del comando musicale.");
    }
}

async function handleIpc(data) {
    console.log("Received IPC Update:", data);
    
    if (data.action === "start_broadcast") {
        const guildId = data.guild_id;
        const sourceId = data.source_channel_id;
        const destIds = data.dest_channels || [];
        const externalDestIds = data.external_dest_channels || [];
        const allDestIds = [...destIds, ...externalDestIds];
        const sourceRoleId = data.source_role_id;

        // Ferma la musica ovunque per questo guild prima del broadcast
        for (const bot of [primaryBot, ...auxBots]) {
            const p = musicPlayers.get(bot.user.id);
            const q = p?.nodes.get(guildId);
            if (q) q.delete();
        }

        // 1. Primary Bot Joins
        const guild = primaryBot.guilds.cache.get(guildId);
        if (!guild) return console.log("Guild not found.");
        
        const sourceChannel = guild.channels.cache.get(sourceId);
        if (!sourceChannel) return console.log("Source channel not found.");

        let oldConnection = getVoiceConnection(guildId);
        if (oldConnection) oldConnection.destroy();

        const connection = joinVoiceChannel({
            channelId: sourceId,
            guildId: guildId,
            adapterCreator: guild.voiceAdapterCreator,
            selfDeaf: false
        });

        console.log(`Primary bot joined ${sourceChannel.name}`);

        // Ricrea il player per pulire buffer vecchi
        audioPlayer.stop();

        connection.on(VoiceConnectionStatus.Ready, () => {
            const receiver = connection.receiver;
            // Listen to any user speaking
            receiver.speaking.on('start', async (userId) => {
                // Filtro per Ruolo
                if (sourceRoleId) {
                    try {
                        // Prova dalla cache prima, altrimenti scarica da discord
                        let member = guild.members.cache.get(userId);
                        if (!member) member = await guild.members.fetch(userId);
                        
                        if (!member.roles.cache.has(sourceRoleId)) {
                            // L'utente non ha il ruolo autorizzato, ignoriamo il suo audio.
                            return; 
                        }
                    } catch (err) {
                        return;
                    }
                }

                console.log(`Authorized User ${userId} started speaking...`);
                // Capture Opus packets 
                const audioStream = receiver.subscribe(userId, {
                    end: {
                        behavior: EndBehaviorType.AfterSilence,
                        duration: 100,
                    },
                });
                
                // Play the Opus stream directly without padding
                const resource = createAudioResource(audioStream, { 
                    inputType: StreamType.Opus,
                    silencePaddingFrames: 0
                });
                audioPlayer.play(resource);
            });
        });

        // 2. Aux Bots Join
        if (!activeBroadcasts.has(guildId)) {
            activeBroadcasts.set(guildId, []);
        }
        const currentBroadcast = activeBroadcasts.get(guildId);
        const usedBotsPerGuild = new Map();

        for (const destId of allDestIds) {
            let assignedBot = null;
            let destChannel = null;

            for (const bot of auxBots) {
                let channel = bot.channels.cache.get(destId);
                
                if (!channel) {
                    try {
                        channel = await bot.channels.fetch(destId).catch(() => null);
                    } catch (e) {
                        channel = null;
                    }
                }

                if (channel && channel.isVoiceBased()) {
                    const targetGuildId = channel.guild.id;
                    if (!usedBotsPerGuild.has(targetGuildId)) {
                        usedBotsPerGuild.set(targetGuildId, new Set());
                    }
                    
                    const usedInThisGuild = usedBotsPerGuild.get(targetGuildId);
                    
                    if (!usedInThisGuild.has(bot.user.id)) {
                        assignedBot = bot;
                        destChannel = channel;
                        usedInThisGuild.add(bot.user.id);
                        break;
                    }
                }
            }

            if (assignedBot && destChannel) {
                const targetGuildId = destChannel.guild.id;
                
                let auxConn = getVoiceConnection(targetGuildId, assignedBot.user.id);
                if (auxConn) auxConn.destroy();

                const auxConnection = joinVoiceChannel({
                    channelId: destId,
                    guildId: targetGuildId,
                    adapterCreator: destChannel.guild.voiceAdapterCreator,
                    group: assignedBot.user.id
                });
                
                auxConnection.subscribe(audioPlayer);
                console.log(`Aux bot joined ${destChannel.name} in server ${destChannel.guild.name} and is listening to player.`);
                
                currentBroadcast.push({ botId: assignedBot.user.id, targetGuildId });
            } else {
                console.log(`Channel ${destId} not found or no free aux bot available for its server.`);
            }
        }
    }

    if (data.action === "stop_broadcast") {
        const guildId = data.guild_id;
        const conn = getVoiceConnection(guildId);
        if (conn) conn.destroy();
        
        const currentBroadcast = activeBroadcasts.get(guildId);
        if (currentBroadcast) {
            for (const { botId, targetGuildId } of currentBroadcast) {
                const auxConn = getVoiceConnection(targetGuildId, botId);
                if (auxConn) auxConn.destroy();
            }
            activeBroadcasts.delete(guildId);
        } else {
            for (const bot of auxBots) {
                const auxConn = getVoiceConnection(guildId, bot.user.id);
                if (auxConn) auxConn.destroy();
            }
        }
        audioPlayer.stop();
        console.log("Stopped broadcast.");
    }
    
    if (data.action.startsWith("music_")) {
        const command = data.action.replace("music_", "");
        const guildId = data.guild_id;
        const query = data.query;
        const targetBotId = data.bot_id;
        
        let selectedBot = null;
        let selectedPlayer = null;

        if (targetBotId) {
            selectedBot = auxBots.find(b => b.user.id === targetBotId);
            if (selectedBot) selectedPlayer = musicPlayers.get(targetBotId);
        }

        if (!selectedPlayer && (command === 'play' || command === 'insert')) {
            // Seleziona un bot (come nel comando chat)
            for (const bot of auxBots) {
                const p = musicPlayers.get(bot.user.id);
                const queue = p?.nodes.get(guildId);
                if (queue && queue.channel.id === data.voice_channel_id) {
                    selectedBot = bot;
                    selectedPlayer = p;
                    break;
                }
            }
            if (!selectedBot) {
                for (const bot of auxBots) {
                    const p = musicPlayers.get(bot.user.id);
                    const queue = p?.nodes.get(guildId);
                    const nativeConnection = getVoiceConnection(guildId, bot.user.id);
                    if (!queue && !nativeConnection) {
                        selectedBot = bot;
                        selectedPlayer = p;
                        break;
                    }
                }
            }
        } else if (!selectedPlayer) {
            // Per gli altri comandi senza targetBotId, cerca il primo player con una coda in questo guild
            for (const bot of auxBots) {
                const p = musicPlayers.get(bot.user.id);
                if (p?.nodes.get(guildId)) {
                    selectedBot = bot;
                    selectedPlayer = p;
                    break;
                }
            }
        }

        if (selectedPlayer) {
            try {
                if (command === 'play' || command === 'insert') {
                    const guild = selectedBot.guilds.cache.get(guildId);
                    const vc = guild?.channels.cache.get(data.voice_channel_id);
                    if (vc) {
                        const permissions = vc.permissionsFor(selectedBot.user);
                        if (!permissions?.has('ViewChannel') || !permissions?.has('Connect') || !permissions?.has('Speak')) {
                            console.error(`[IPC] Il bot ${selectedBot.user.id} non ha i permessi necessari (ViewChannel, Connect, Speak) per il canale ${vc.name}`);
                            return;
                        }

                        // Fix per i link di YouTube Music
                        let safeQuery = query;
                        if (safeQuery.includes('music.youtube.com')) {
                            safeQuery = safeQuery.replace('music.youtube.com', 'www.youtube.com');
                        }

                        const searchResult = await searchWithFallback(selectedPlayer, safeQuery, primaryBot.user);
                        if (searchResult.hasTracks()) {
                            const insert = command === 'insert';
                            const { track } = await selectedPlayer.play(vc, searchResult, {
                                nodeOptions: { metadata: null },
                                requestedBy: primaryBot.user
                            });

                            let queue = selectedPlayer.nodes.get(guildId);
                            if (insert && queue && queue.tracks.size > 1) {
                                if (searchResult.playlist) {
                                    const addedTracks = queue.tracks.toArray().slice(-searchResult.tracks.length);
                                    addedTracks.forEach(t => queue.removeTrack(t));
                                    addedTracks.reverse().forEach(t => queue.insertTrack(t, 0));
                                } else {
                                    queue.removeTrack(track);
                                    queue.insertTrack(track, 0);
                                }
                            }
                        }
                    }
                } else {
                    const queue = selectedPlayer.nodes.get(guildId);
                    if (queue) {
                        if (command === 'skip') {
                            console.log(`[IPC MUSIC] skip called for guild ${guildId}`);
                            queue.node.skip();
                        }
                        if (command === 'previous') queue.history.previous();
                        if (command === 'pause') queue.node.pause();
                        if (command === 'resume') queue.node.resume();
                        if (command === 'stop') queue.delete();
                    }
                }
            } catch (e) {
                console.error("Errore IPC music command:", e);
            }
        }
    }

    if (data.action === "system_restart") {
        console.log("[SYSTEM] Ricevuto comando di riavvio dal Mainframe. Riavvio in corso...");
        process.exit(0);
    }
}

// Timeout management
const emptyChannelTimeouts = new Map();

primaryBot.on('voiceStateUpdate', (oldState, newState) => {
    // Gestione auto-disconnect se il canale si svuota
    const guildId = oldState.guild.id;
    const conn = getVoiceConnection(guildId);
    if (!conn) return; // Non siamo in vocale in questo server

    const sourceChannelId = conn.joinConfig.channelId;
    
    // Se qualcuno è entrato o uscito dal nostro canale sorgente
    if (oldState.channelId === sourceChannelId || newState.channelId === sourceChannelId) {
        const channel = oldState.guild.channels.cache.get(sourceChannelId);
        if (!channel) return;

        // Conta gli umani (escludendo i bot)
        const humans = channel.members.filter(m => !m.user.bot).size;

        if (humans === 0) {
            console.log(`[TIMEOUT] Canale sorgente vuoto. Disconnessione tra 3 minuti...`);
            const timeout = setTimeout(() => {
                console.log(`[TIMEOUT] Nessuno è entrato. Disconnessione automatica.`);
                publishMessage("dab_updates", { action: "stop_broadcast", guild_id: guildId }).catch(console.error);
                emptyChannelTimeouts.delete(guildId);
            }, 3 * 60 * 1000); // 3 minuti
            emptyChannelTimeouts.set(guildId, timeout);
        } else {
            // Se c'è almeno un umano e c'era un timeout pendente, cancellalo
            if (emptyChannelTimeouts.has(guildId)) {
                console.log(`[TIMEOUT] Utente entrato. Disconnessione annullata.`);
                clearTimeout(emptyChannelTimeouts.get(guildId));
                emptyChannelTimeouts.delete(guildId);
            }
        }
    }
});

// Chiusura sicura (Graceful Shutdown)
process.on('SIGINT', () => {
    console.log("\n[SHUTDOWN] Chiusura in corso... disconnessione di tutti i bot.");
    if (primaryBot.isReady()) primaryBot.destroy();
    for (const bot of auxBots) {
        if (bot.isReady()) bot.destroy();
    }
    process.exit(0);
});

async function startIPCListener() {
    dbClient = new MongoClient(MONGO_URI);
    await dbClient.connect();
    console.log("✅ Connected to MongoDB");

    const db = dbClient.db(DB_NAME);
    const logCollection = db.collection('bot_logs');

    // Log levels implementation
    const logLevels = { debug: 0, info: 1, warn: 2, error: 3 };
    const currentLevelStr = (process.env.LOG_LEVEL || 'info').toLowerCase();
    const currentLevel = logLevels[currentLevelStr] ?? 1;

    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn || originalLog;
    const originalDebug = console.debug || originalLog;

    console.debug = function(...args) {
        if (currentLevel <= logLevels.debug) {
            originalDebug.apply(console, ['[DEBUG]', ...args]);
            const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            logCollection.insertOne({ timestamp: new Date(), level: 'debug', message: msg }).catch(() => {});
        }
    };

    console.log = function(...args) {
        if (currentLevel <= logLevels.info) {
            originalLog.apply(console, ['[INFO]', ...args]);
            const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            logCollection.insertOne({ timestamp: new Date(), level: 'info', message: msg }).catch(() => {});
        }
    };

    console.warn = function(...args) {
        if (currentLevel <= logLevels.warn) {
            originalWarn.apply(console, ['[WARN]', ...args]);
            const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            logCollection.insertOne({ timestamp: new Date(), level: 'warn', message: msg }).catch(() => {});
        }
    };

    console.error = function(...args) {
        if (currentLevel <= logLevels.error) {
            originalError.apply(console, ['[ERROR]', ...args]);
            const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            logCollection.insertOne({ timestamp: new Date(), level: 'error', message: msg }).catch(() => {});
        }
    };

    const collection = db.collection('ipc_messages');
    
    const lastDoc = await collection.find().sort({ $natural: -1 }).limit(1).toArray();
    let lastId;
    if (lastDoc.length === 0) {
        const res = await collection.insertOne({ channel: 'dummy', data: 'init' });
        lastId = res.insertedId;
    } else {
        lastId = lastDoc[0]._id;
    }

    console.log(`✅ IPC Tailable Cursor listening after ID: ${lastId}`);

    const cursor = collection.find({ channel: "dab_updates", _id: { $gt: lastId } }, {
        tailable: true,
        awaitData: true,
        timeout: false
    });

    // Handle stream
    cursor.stream().on('data', async (doc) => {
        lastId = doc._id;
        await handleIpc(doc.data);
    });
}
// Intercettazione globale per aggirare i blocchi di YouTube
// Utilizza youtube-dl-exec (yt-dlp) per estrarre direttamente i flussi m4a
// bypassando le API web e android che vengono attualmente bloccate (errore 403 o 400).
/*
onBeforeCreateStream(async (track, queryType, queue) => {
    const isYouTube = track.url.includes('youtube.com') || track.url.includes('youtu.be') || track.extractor?.identifier === 'com.retrouser955.discord-player.discord-player-youtubei';
    const isSpotify = track.url.includes('spotify.com') || track.extractor?.identifier === 'com.discord-player.spotifyextractor';
    
    if (isYouTube || isSpotify) {
        try {
            console.log(`[GLOBAL BRIDGE] Intercettata traccia ${isSpotify ? 'Spotify' : 'YouTube'}: ${track.title}. Uso youtube-dl per estrarre il flusso...`);
            let searchUrl = track.url;
            
            if (isSpotify) {
                const cleanTitle = `${track.title} ${track.author}`.replace(/\[.*?\]|\(.*?\)/g, '').trim();
                searchUrl = `ytsearch1:${cleanTitle}`;
            }

            const ytOptions = {
                dumpJson: true,
                format: 'bestaudio[ext=m4a]/bestaudio'
            };
            if (existsSync(resolve('./cookies.txt'))) {
                ytOptions.cookies = resolve('./cookies.txt');
                console.log(`[GLOBAL BRIDGE] Trovato cookies.txt, lo applico per l'autenticazione YouTube.`);
            }

            const res = await yt(searchUrl, ytOptions);
            
            let streamUrl = res?.url;
            if (!streamUrl && Array.isArray(res?.entries) && res.entries.length > 0) {
                 streamUrl = res.entries[0].url;
            }

            if (streamUrl) {
                console.log(`[GLOBAL BRIDGE] Flusso audio estratto con successo (m4a url). Trasmetto al player...`);
                return streamUrl;
            } else {
                console.log(`[GLOBAL BRIDGE] Nessun flusso estratto da youtube-dl.`);
            }
        } catch (e) {
            console.error(`[GLOBAL BRIDGE ERROR] Errore critico nel bridge youtube-dl:`, e);
        }
    }
    return null;
});
*/

async function searchWithFallback(player, query, requestedBy) {
    if (query.includes('youtube.com/playlist') || (query.includes('youtube.com/watch') && query.includes('list='))) {
        try {
            console.log(`[SYS] Estrazione manuale playlist YouTube: ${query}`);
            const ytOptions = { dumpSingleJson: true, flatPlaylist: true };
            if (existsSync(resolve('./cookies.txt'))) {
                ytOptions.cookies = resolve('./cookies.txt');
            }
            const res = await yt(query, ytOptions);
            if (res && res.entries && res.entries.length > 0) {
                const tracks = res.entries.map(e => new Track(player, {
                    title: e.title,
                    description: e.description || '',
                    author: e.uploader || e.channel || 'Unknown',
                    url: e.url || `https://www.youtube.com/watch?v=${e.id}`,
                    thumbnail: e.thumbnails?.[0]?.url || '',
                    duration: e.duration ? new Date(e.duration * 1000).toISOString().substring(11, 19).replace(/^00:/, '') : '0:00',
                    views: e.view_count || 0,
                    requestedBy: requestedBy,
                    source: 'youtube'
                }));
                const playlist = new Playlist(player, {
                    title: res.title || 'YouTube Playlist',
                    url: query,
                    tracks: tracks,
                    source: 'youtube',
                    thumbnail: tracks[0]?.thumbnail || '',
                    author: { name: res.uploader || 'Unknown', url: '' }
                });
                return new SearchResult(player, {
                    query: query,
                    queryType: 'youtubePlaylist',
                    playlist: playlist,
                    tracks: tracks,
                    requestedBy: requestedBy
                });
            }
        } catch (e) {
            console.error(`Errore estrazione manuale playlist:`, e);
        }
    }
    return await player.search(query, { requestedBy });
}

// START
async function startBots() {
    await startIPCListener();
    await registerCommands();

    console.log("Logging in Primary Bot...");
    await primaryBot.login(PRIMARY_TOKEN);
    console.log(`✅ Logged in as ${primaryBot.user.tag}`);

    for (let i = 0; i < auxBots.length; i++) {
        console.log(`Logging in Aux Bot ${i+1}...`);
        await auxBots[i].login(AUX_TOKENS[i]);
    }

    console.log("Inizializzazione discord-player per i pinguini...");
    for (const bot of [primaryBot, ...auxBots]) {
        const player = new Player(bot);
        await player.extractors.loadMulti(DefaultExtractors);
        await player.extractors.register(YoutubeiExtractor, {
            streamOptions: {
                useClient: 'IOS'
            }
        });
        
        player.events.on('error', (queue, error) => {
            console.error(`[PLAYER ERROR] Errore generico (Bot ${bot.user.id}):`, error);
        });

        player.events.on('playerError', (queue, error) => {
            console.error(`[AUDIO ENGINE ERROR] Errore di decodifica/stream (Bot ${bot.user.id}):`, error);
        });
        
        player.events.on('connectionError', (queue, error) => {
            console.error(`[CONNECTION ERROR] Errore connessione vocale (Bot ${bot.user.id}):`, error);
        });

        player.events.on('debug', (queue, message) => {
            console.debug(`(Bot ${bot.user.id}):`, message);
        });

        player.on('debug', (message) => {
            console.debug(`[SYS] (Bot ${bot.user.id}):`, message);
        });

        player.events.on('playerStart', (queue, track) => {
            console.log(`[PLAYING] Avviata riproduzione di: ${track.title} (Bot ${bot.user.id})`);
        });

        musicPlayers.set(bot.user.id, player);
    }
    console.log("✅ Music Players inizializzati.");

    // Avvia il sync dello stato musicale su MongoDB
    startMusicStatusSync();
}

process.on('uncaughtException', (err) => {
    console.error('[CRITICAL CRASH] Uncaught Exception:', err);
});
process.on('unhandledRejection', (reason, promise) => {
    console.error('[CRITICAL CRASH] Unhandled Rejection:', reason);
});

function startMusicStatusSync() {
    setInterval(async () => {
        if (!dbClient) return;
        const db = dbClient.db(DB_NAME);
        const collection = db.collection('guild_music_status');
        
        // Raccogliamo lo stato per ogni gilda attiva
        const statusByGuild = new Map();

        for (const bot of [primaryBot, ...auxBots]) {
            const player = musicPlayers.get(bot.user.id);
            if (!player) continue;

            for (const queue of player.nodes.cache.values()) {
                const guildId = queue.guild.id;
                if (!statusByGuild.has(guildId)) {
                    statusByGuild.set(guildId, []);
                }
                
                const current = queue.currentTrack;
                statusByGuild.get(guildId).push({
                    bot_id: bot.user.id,
                    channel_id: queue.channel?.id,
                    is_paused: queue.node.isPaused(),
                    current_track: current ? {
                        title: current.title,
                        url: current.url,
                        thumbnail: current.thumbnail,
                        duration: current.duration
                    } : null,
                    queue: queue.tracks.toArray().slice(0, 50).map(t => ({
                        title: t.title,
                        url: t.url,
                        thumbnail: t.thumbnail
                    }))
                });
            }
        }

        // Aggiorna MongoDB
        // Poiché ci sono guild senza musica attiva, dovremmo anche pulire i vecchi documenti 
        // o fare upsert basandoci sulla map, e rimuovere quelli che non sono più attivi.
        try {
            const bulkOps = [];
            
            // Aggiorna o Inserisci gli attivi
            for (const [guildId, active_bots] of statusByGuild.entries()) {
                bulkOps.push({
                    updateOne: {
                        filter: { guild_id: guildId },
                        update: { $set: { active_bots, last_updated: new Date() } },
                        upsert: true
                    }
                });
            }

            // Segna come vuoti quelli non più attivi
            bulkOps.push({
                updateMany: {
                    filter: { guild_id: { $nin: Array.from(statusByGuild.keys()) } },
                    update: { $set: { active_bots: [], last_updated: new Date() } }
                }
            });

            if (bulkOps.length > 0) {
                await collection.bulkWrite(bulkOps);
            }
        } catch (e) {
            console.error("Errore nel sync dello stato musicale:", e);
        }
    }, 1000); // Ogni 1 secondo
}

startBots().catch(console.error);
