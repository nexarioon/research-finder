import makeWASocket, {
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestBaileysVersion
} from '@whiskeysockets/baileys';
import express from 'express';
import pino from 'pino';
import qrcode from 'qrcode-terminal';
import fs from 'fs';

// Prevent process crashes on network/socket drops
process.on('uncaughtException', (err) => {
    console.error('⚠️ [Gateway Anti-Crash] Uncaught Exception:', err?.message || err);
});
process.on('unhandledRejection', (reason) => {
    console.error('⚠️ [Gateway Anti-Crash] Unhandled Rejection:', reason?.message || reason);
});

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const logger = pino({ level: 'silent' });
const AUTH_FOLDER = 'auth_info_baileys';

let sock = null;
let connectionState = 'connecting';
let isConnecting = false;

function clearAuthFolder() {
    try {
        if (fs.existsSync(AUTH_FOLDER)) {
            fs.rmSync(AUTH_FOLDER, { recursive: true, force: true });
            console.log('🧹 Session auth folder cleared for fresh QR scan.');
        }
    } catch (e) {
        console.error('Failed to clear auth folder:', e.message);
    }
}

async function connectToWhatsApp() {
    if (isConnecting) return;
    isConnecting = true;

    try {
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
        const { version } = await fetchLatestBaileysVersion();

        sock = makeWASocket({
            version,
            auth: state,
            logger,
            printQRInTerminal: false,
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 60000,
            keepAliveIntervalMs: 10000,
            retryRequestDelayMs: 2000
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                connectionState = 'qr_required';
                console.log('\n==================================================');
                console.log('📱 SCAN QR CODE DENGAN WHATSAPP DI SMARTPHONE ANDA:');
                console.log('==================================================\n');
                qrcode.generate(qr, { small: true });
                console.log('\n(Buka WA -> Perangkat Tertaut -> Tautkan Perangkat)\n');
            }

            if (connection === 'close') {
                isConnecting = false;
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const isLoggedOut = statusCode === DisconnectReason.loggedOut || statusCode === 401;
                
                console.log(`❌ Koneksi terputus (Status Code: ${statusCode || 'unknown'}).`);

                if (isLoggedOut) {
                    console.log('🔑 Session WhatsApp telah logged-out / unlinked. Menghapus auth info...');
                    connectionState = 'qr_required';
                    clearAuthFolder();
                    setTimeout(connectToWhatsApp, 2000);
                } else {
                    console.log('🔄 Reconnecting to WhatsApp in 2 seconds...');
                    connectionState = 'connecting';
                    setTimeout(connectToWhatsApp, 2000);
                }
            } else if (connection === 'open') {
                isConnecting = false;
                connectionState = 'connected';
                const userPhone = sock.user?.id ? sock.user.id.split(':')[0] : 'Aktif';
                console.log('\n==================================================');
                console.log(`✅ WHATSAPP BERHASIL TERHUBUNG SEBAGAI: ${userPhone}`);
                console.log(`🚀 WA Gateway Aktif di: http://localhost:${PORT}/send-message`);
                console.log('==================================================\n');
            }
        });
    } catch (e) {
        isConnecting = false;
        console.error('Error starting Baileys socket:', e.message);
        setTimeout(connectToWhatsApp, 4000);
    }
}

// REST API Endpoints
app.get('/status', (req, res) => {
    res.json({
        status: connectionState,
        connected: connectionState === 'connected',
        user: sock?.user?.id ? sock.user.id.split(':')[0] : null
    });
});

app.post('/send-message', async (req, res) => {
    if (connectionState === 'connecting') {
        let waitAttempts = 0;
        while (connectionState === 'connecting' && waitAttempts < 10) {
            await new Promise(r => setTimeout(r, 500));
            waitAttempts++;
        }
    }

    if (connectionState !== 'connected' || !sock) {
        return res.status(503).json({
            status: 'error',
            detail: 'WhatsApp Gateway belum terhubung. Silakan scan QR code di terminal wa-gateway.'
        });
    }

    const rawTarget = req.body.target || req.body.phone || req.body.number;
    const messageText = req.body.message || req.body.text;

    if (!rawTarget || !messageText) {
        return res.status(400).json({
            status: 'error',
            detail: 'Parameter target/phone dan message wajib diisi'
        });
    }

    let cleanPhone = String(rawTarget).replace(/[^0-9]/g, '');
    if (cleanPhone.startsWith('0')) {
        cleanPhone = '62' + cleanPhone.slice(1);
    } else if (cleanPhone.startsWith('8')) {
        cleanPhone = '62' + cleanPhone;
    }

    const jid = `${cleanPhone}@s.whatsapp.net`;

    try {
        const onWaResult = await sock.onWhatsApp(cleanPhone).catch(() => null);
        const exists = onWaResult && onWaResult[0] && onWaResult[0].exists;
        
        if (!exists) {
            console.log(`⚠️ Nomor ${cleanPhone} tidak terdaftar di WhatsApp. Skipped.`);
            return res.status(404).json({
                status: 'error',
                detail: `Nomor ${cleanPhone} tidak terdaftar di WhatsApp`
            });
        }

        const targetJid = onWaResult[0].jid || jid;
        const sentMsg = await sock.sendMessage(targetJid, { text: messageText });
        console.log(`✅ Pesan berhasil dikirim ke ${cleanPhone} [ID: ${sentMsg?.key?.id || 'ok'}]`);

        return res.json({
            status: 'ok',
            target: cleanPhone,
            jid: targetJid,
            message_id: sentMsg?.key?.id || null
        });
    } catch (err) {
        console.error(`❌ Error sending message to ${cleanPhone}:`, err.message);
        return res.status(500).json({
            status: 'error',
            detail: err.message
        });
    }
});

app.listen(PORT, () => {
    console.log(`\n🤖 Baileys WA Gateway Service started on port ${PORT}`);
    console.log(`⚙️  Connecting to WhatsApp protocol...\n`);
    connectToWhatsApp();
});
