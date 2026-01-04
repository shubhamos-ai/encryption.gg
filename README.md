<!-- ========================= -->
<!--  SHUBHAMOS SECURE CRYPT   -->
<!-- ========================= -->

<p align="center">
  <b>Ephemeral • Private • Zero-Trust Encryption</b><br>
  <i>Encrypt → Exchange → Erase</i>
</p>

---

<p align="center">
  <video
    src="https://github.com/user-attachments/assets/9d22cdac-cf08-457a-bac8-020abbf67092"
    autoplay
    loop
    muted
    playsinline
    width="900">
  </video>
</p>

---

<p align="center">
  🔗 <b>Live Test Deployment</b><br>
  <a href="https://encryption-3qxz.onrender.com">
    https://encryption-3qxz.onrender.com
  </a>
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/Privacy-First-black?style=for-the-badge">
  <img src="https://img.shields.io/badge/Ephemeral-Data-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/Zero-Trust-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/Open-Experimentation-purple?style=for-the-badge">
</p>

---

## 🔐 What Is This?

**SHUBHAMOS Secure Crypt** is a privacy-focused encryption service built for  
**temporary, one-time, irreversible data exchange**.

It allows users to encrypt **images and text**, retrieve them securely, and ensures
that **all data self-destructs** after use or expiry.

No persistence.  
No recovery.  
No silent storage.

---

## 🧠 Design Philosophy

> **If data must exist, it should exist briefly.**

This system follows a **zero-trust mindset**:

- Each request is isolated
- Each key is unique
- Each file has a defined lifespan
- Any failure results in destruction, not exposure

---

## ✨ Core Features

### 🔑 One-Time Encryption
- Unique key per request
- Keys cannot be reused
- No regeneration possible

### ⏳ Automatic Destruction
- Time-based expiry
- Instant deletion after download
- Continuous cleanup process

### 🚦 Request Queue Control
- Prevents abuse and overload
- Fair request handling
- Live position tracking

### 🧾 Session-Scoped History
- Temporary session visibility
- Expired entries vanish automatically
- No permanent tracking

### 🔒 Failure-Safe Handling
- Invalid keys return nothing
- Corrupted payloads are rejected
- Partial downloads are destroyed

---

## 🖼️ Image Encryption Flow

```

┌──────────┐
│  Image   │
└────┬─────┘
▼
┌──────────┐
│ Encrypt  │
└────┬─────┘
▼
┌──────────────┐
│ Encrypted Bin│
└────┬─────────┘
▼
┌──────────────┐
│ One-Time Key │
└────┬─────────┘
▼
┌──────────────┐
│ Auto Destroy │
└──────────────┘

```

⚠️ **Losing the key permanently destroys the data**

---

## ✉️ Text Encryption Flow

```

Text → Encrypt → Payload + Key → Decrypt → Auto Expire

```

- No storage
- No logging
- No recovery path

---

## 🔐 Security Model Overview

- Isolated encryption per request
- Short-lived encrypted artifacts
- No shared secrets
- No server-side recovery

> **Security failures destroy data instead of exposing it.**

---

## 🧪 Ideal Use Cases

- Secure image sharing
- Ephemeral communication
- Temporary secret exchange
- Privacy-focused workflows
- Security demonstrations
- Encryption proof-of-concepts

---

## ⚠️ Critical Warnings

🚨 **THIS SYSTEM IS INTENTIONALLY UNFORGIVING**

- Keys are **not recoverable**
- Expired data is **permanently deleted**
- No admin override
- No backups
- No undo

**This is not cloud storage.  
This is controlled data loss.**

---

## 🕶️ Dark-Mode Optimized

Designed to feel native in:
- Dark terminals
- Cyber-style dashboards
- Minimal security panels
- Hacker-inspired interfaces

---

## 📜 Disclaimer

This project is provided for **educational and experimental use**.

Do **not**:
- Use it for long-term storage
- Treat it as a backup solution
- Assume recovery is possible

The author is **not responsible** for data loss caused by:
- Lost keys
- Expired files
- User mistakes
- Intentional destruction mechanisms

---

## 🧑‍💻 Author

**Shubham**  
Project Identity: **SHUBHAMOS**

---

## ⭐ Support

If this project made you rethink privacy:

- ⭐ Star the repository
- 🧠 Learn from the architecture
- 🔐 Respect ephemeral security
- 🚀 Build something better

---

<p align="center">
  <b>Encrypt. Exchange. Erase.</b><br>
  <i>Nothing lasts. That’s the point.</i>
</p>
```
