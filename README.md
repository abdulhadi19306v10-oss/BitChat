# 💬 Cipher — Secure Worldwide Communication Platform

Cipher is a premium, cross-platform real-time communication app with a Discord × WhatsApp fusion UI. Built on a hybrid Python socket + FastAPI backend with a Flutter frontend.

---

## ✅ Implemented Features

| Feature | Description |
|---------|-------------|
| 🔐 **Auth (Register / Login)** | bcrypt-hashed passwords, email validation, device fingerprinting anti-alt |
| 🌐 **Real-Time Messaging** | Custom 4-byte framed TCP socket server, zero-latency delivery |
| 👁️ **Online / Offline Presence** | Live green/grey dot on every avatar, "Online / Offline" in chat header |
| ✍️ **Typing Indicator** | Animated bouncing dots — server-relayed, debounced at 2 s |
| ✅ **Read Receipts** | Grey ✓✓ = delivered, Blue ✓✓ = read — relayed via server |
| 🗑️ **Message Deletion** | Long-press → Delete (own messages only) — synced to peer in real-time |
| 😍 **Emoji Reactions** | Long-press → Quick-react (6 emojis) — pills shown under bubbles, toggle off/on |
| 🌙 **Dark / Light Theme** | Full theme toggle in sidebar, all components respect it |
| 👥 **Friend Requests UI** | Accept / reject pending requests, add by username, dedicated Friends screen |
| 📷 **QR Friend System** | Every user gets a unique QR code — scan to add friend instantly |
| 📵 **Offline Message Queue** | Messages to offline users stored in DB, delivered on reconnect |
| 📞 **Call Screen UI** | Full voice/video call screen — accept/reject/end, mute/speaker/camera, live timer |
| 🔊 **Group Messaging** | Server-side group create/join/leave/delete with broadcast relay |
| 📎 **File Sharing** | File picker integration, file preview pill before sending |
| 😊 **Emoji Picker** | Full emoji keyboard drawer with category navigation |
| 🔒 **AES-256 Encryption** | Per-message random IV (prepended as `iv:ciphertext`) |
| 🛡️ **Anti-Alt System** | DB-level IP rate-limit (survives restarts) + device fingerprint block |
| 📡 **VoIP Media Relay** | UDP socket relay for voice/video call media frames |
| 💾 **Offline-First DB** | SQLite for local dev, PostgreSQL-ready via `DATABASE_URL` env var |

---

## 🚧 Planned / Not Yet Implemented

These features require external service setup or are scoped for a future phase:

### 🔔 Phase 5 — Push Notifications (Firebase)
Firebase Cloud Messaging (FCM) for background push notifications when the app is closed.

**Why not done:** Requires a Firebase project, `google-services.json` / `GoogleService-Info.plist` per platform, and a server-side FCM token registry. This is platform-specific setup that must be done per deployment target (Android / iOS / Web).

**To implement:**
1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Add `firebase_messaging: ^14.x.x` and `firebase_core` to `pubspec.yaml`
3. Add `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) to the app
4. Store FCM tokens in the API DB (`users.fcm_token` column)
5. In `chat_server.py`, when a message is sent to an offline user, POST to Firebase FCM API in addition to (or instead of) the offline queue

---

### 🔑 Phase 6 — JWT Authentication Tokens
Replace the current plain `user_id` query-parameter auth with proper JWT bearer tokens.

**Why not done:** Requires a breaking change to every API endpoint — all routes need a `Depends(get_current_user)` dependency that decodes and validates the token. The Flutter client would need to attach `Authorization: Bearer <token>` to every HTTP request and handle token refresh.

**To implement:**
1. Add `python-jose[cryptography]` and `passlib` to `requirements.txt`
2. Create a `create_access_token(data, expires_delta)` utility in `api/auth.py`
3. Return `access_token` from `/api/login` and `/api/register`
4. Add `get_current_user` FastAPI dependency that decodes the JWT
5. Replace every `user_id: int` query param with `current_user = Depends(get_current_user)`
6. In Flutter: store token in `SharedPreferences`, add `Authorization` header to all `ApiService` requests
7. Implement token refresh (optional: use refresh tokens with longer expiry)

---

### 🔐 Phase 7 — Full RSA End-to-End Encryption (E2EE)
Complete the RSA key exchange so the AES session key is never transmitted in plaintext.

**Why not done:** The AES encryption layer is fully working (random IV per message). The RSA skeleton exists in `encryption_service.dart`. Wiring it up requires a key registration API endpoint and the full key-exchange handshake on session start.

**Current state:** `EncryptionService` generates and uses AES-256 session keys. `generateSessionKey()` and `setSessionKey()` are implemented. RSA key generation (`pointycastle`) is available as a dependency but commented out pending this phase.

**To implement:**
1. On app start, generate an RSA-2048 keypair using `pointycastle`
2. Upload the public key to `/api/users/{id}/public_key` (new endpoint)
3. When starting a chat with User B, fetch B's public key from the API
4. Generate a new AES session key, encrypt it with B's RSA public key, send via socket (`key_exchange` message type)
5. B decrypts the AES key with their RSA private key, calls `setSessionKey()`
6. All subsequent messages use `encryptMessage()` / `decryptMessage()` — already implemented

---

## 🏗️ Architecture

```
                  ┌──────────────────────────────────────┐
                  │         Cipher Cloud Backend          │
                  │   FastAPI :8000    TCP/UDP :5000      │
                  └───────────────┬──────────────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
        REST (Auth / Friends / Queue)         TCP/UDP (Real-Time)
              │                                       │
   ┌──────────▼──────────┐                 ┌──────────▼──────────┐
   │  • SQLite / PgSQL   │                 │  • AES-256 E2EE     │
   │  • User / QR Auth   │                 │  • 4-byte Framing   │
   │  • Friend Requests  │                 │  • VoIP UDP Relay   │
   │  • Offline Queue    │                 │  • Read Receipts    │
   │  • Anti-Alt System  │                 │  • Reactions / Del  │
   └─────────────────────┘                 └─────────────────────┘
```

---

## 📂 Project Structure

```
Cipher/
├── api/
│   ├── database.py       # SQLAlchemy engine + session
│   ├── models.py         # User, Friendship, OfflineMessage tables
│   └── main.py           # All FastAPI REST endpoints
├── cipher_app/
│   └── lib/
│       ├── main.dart                    # App entry, routes
│       ├── screens/
│       │   ├── home_screen.dart         # Main chat UI (all features)
│       │   ├── login_screen.dart
│       │   ├── register_screen.dart
│       │   ├── call_screen.dart         # Voice/video call UI
│       │   ├── friends_screen.dart      # Friend requests UI
│       │   └── qr_scanner_screen.dart
│       └── services/
│           ├── api_service.dart         # All HTTP calls
│           ├── socket_service.dart      # TCP socket + framing
│           └── encryption_service.dart  # AES-256 encrypt/decrypt
├── chat_server.py         # Multi-threaded TCP + UDP socket server
├── Dockerfile             # Cloud deployment config
├── requirements.txt
└── README.md
```

---

## 🛠️ Getting Started

### Prerequisites
- **Backend:** Python 3.11+, (SQLite included for local dev, PostgreSQL for production)
- **Frontend:** Flutter SDK 3.2.0+

### 1. Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Terminal 1 — REST API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Socket Server
python chat_server.py
```

### 2. Frontend

```bash
cd cipher_app
flutter pub get
flutter run -d windows   # or: flutter run
```

### 3. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./cipher.db` | Switch to PostgreSQL in production |

### 4. Demo Accounts (Local)

| Username | Email | Password |
|----------|-------|----------|
| **Alice** | `alice@cipher.com` | `password123` |
| **Bob** | `bob@cipher.com` | `password123` |
| **Charlie** | `charlie@cipher.com` | `password123` |

---

## 🔒 Security Notes

- Passwords hashed with `bcrypt` (cost factor 12)
- AES-256-CBC with **random IV per message** — IV prepended to ciphertext as `iv:ciphertext`
- IP-based registration rate-limit (1 per hour) enforced at DB level — survives server restarts
- Device fingerprint check blocks multi-account abuse
- ⚠️ `user_id` on friend endpoints is currently a plain query param (SEC-1) — JWT auth (Phase 6) will fix this

---

*Built with Flutter · FastAPI · Python Sockets · SQLAlchemy · bcrypt · AES-256*
