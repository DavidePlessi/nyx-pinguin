import { Client, GatewayIntentBits, REST, Routes, SlashCommandBuilder } from 'discord.js';
import { joinVoiceChannel, createAudioPlayer, createAudioResource, StreamType, VoiceConnectionStatus, EndBehaviorType, getVoiceConnection, NoSubscriberBehavior } from '@discordjs/voice';
import { MongoClient } from 'mongodb';
import { config } from 'dotenv';
import { resolve } from 'path';

// Load .env from backend
config({ path: resolve('../backend/.env') });

const MONGO_URI = process.env.MONGO_URI;
const DB_NAME = process.env.MONGO_DB_NAME;
const PRIMARY_TOKEN = process.env.DISCORD_PRIMARY_TOKEN;
const AUX_TOKENS = (process.env.DISCORD_AUX_TOKENS || '').split(',').map(t => t.trim()).filter(t => t);
const CLIENT_ID = process.env.DISCORD_CLIENT_ID;

// Clients
const primaryBot = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMessages] });
const auxBots = AUX_TOKENS.map(() => new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates] }));

let dbClient;
let audioPlayer = createAudioPlayer({
    behaviors: {
        noSubscriber: NoSubscriberBehavior.Play,
        maxMissedFrames: Math.round(5000 / 20)
    }
});

// Registra i comandi Slash
async function registerCommands() {
    const commands = [
        new SlashCommandBuilder().setName('pinguin_on_duty').setDescription('Avvia il broadcasting audio dai canali configurati'),
        new SlashCommandBuilder().setName('pinguin_at_ease').setDescription('Ferma il broadcasting audio')
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
            source_role_id: config.source_role_id
        });
        await interaction.followUp(`🐧 **Pinguin on Duty!** Avvio del broadcasting dal canale <#${config.source_channel_id}> verso ${config.dest_channels.length} canali...`);
    }

    if (interaction.commandName === 'pinguin_at_ease') {
        await publishMessage("dab_updates", {
            action: "stop_broadcast",
            guild_id: interaction.guildId
        });
        await interaction.reply("💤 **Pinguin at Ease.** Broadcasting fermato!");
    }
});

async function handleIpc(data) {
    console.log("Received IPC Update:", data);
    
    if (data.action === "start_broadcast") {
        const guildId = data.guild_id;
        const sourceId = data.source_channel_id;
        const destIds = data.dest_channels;
        const sourceRoleId = data.source_role_id;

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
        const availableBots = [...auxBots];
        for (const destId of destIds) {
            if (availableBots.length === 0) {
                console.log("Not enough aux bots!");
                break;
            }
            const auxBot = availableBots.shift();
            const destGuild = auxBot.guilds.cache.get(guildId);
            const destChannel = destGuild?.channels.cache.get(destId);

            if (destChannel) {
                let auxConn = getVoiceConnection(guildId, auxBot.user.id); // For the specific bot
                if (auxConn) auxConn.destroy();

                const auxConnection = joinVoiceChannel({
                    channelId: destId,
                    guildId: guildId,
                    adapterCreator: destGuild.voiceAdapterCreator,
                    group: auxBot.user.id
                });
                
                auxConnection.subscribe(audioPlayer);
                console.log(`Aux bot joined ${destChannel.name} and is listening to player.`);
            }
        }
    }

    if (data.action === "stop_broadcast") {
        const guildId = data.guild_id;
        const conn = getVoiceConnection(guildId);
        if (conn) conn.destroy();
        
        for (const bot of auxBots) {
            const auxConn = getVoiceConnection(guildId, bot.user.id);
            if (auxConn) auxConn.destroy();
        }
        audioPlayer.stop();
        console.log("Stopped broadcast.");
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

    // Override console.log and console.error
    const originalLog = console.log;
    const originalError = console.error;

    console.log = function(...args) {
        originalLog.apply(console, args);
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        logCollection.insertOne({ timestamp: new Date(), level: 'info', message: msg }).catch(() => {});
    };

    console.error = function(...args) {
        originalError.apply(console, args);
        const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
        logCollection.insertOne({ timestamp: new Date(), level: 'error', message: msg }).catch(() => {});
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
}

startBots().catch(console.error);
