███████╗██╗  ██╗██╗   ██╗██████╗ ██╗  ██╗ █████╗ ███╗   ███╗ ██████╗ ███████╗
██╔════╝██║  ██║██║   ██║██╔══██╗██║  ██║██╔══██╗████╗ ████║██╔═══██╗██╔════╝
███████╗███████║██║   ██║██████╔╝███████║███████║██╔████╔██║██║   ██║███████╗
╚════██║██╔══██║██║   ██║██╔══██╗██╔══██║██╔══██║██║╚██╔╝██║██║   ██║╚════██║
███████║██║  ██║╚██████╔╝██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝

        S E C U R E   •   E P H E M E R A L   •   Z E R O - T R U S T
````

<p align="center">
  <video src="https://github.com/user-attachments/assets/02d02233-5c18-47cf-ad6d-92e1cde6d7ae"
         autoplay
         loop
         muted
         playsinline
         width="80%">
  </video>
</p>

---

<p align="center">
  🔗 <b>Live Test URL</b><br>
  <a href="https://encryption-3qxz.onrender.com">
    https://encryption-3qxz.onrender.com
  </a>
</p>

---

## 🛡️ Threat Model (Explicit & Honest)

### ✅ Defended Against
- Unauthorized access
- Key reuse attacks
- Server-side data harvesting
- Replay attacks
- Partial download abuse
- Expired data resurrection

### ❌ NOT Defended Against
- User losing the key
- Screen recording / screenshots
- Compromised client devices
- Malware on user system
- Physical access to unlocked sessions

> **This system protects data in transit & lifecycle — not user mistakes.**

---

## 🔑 Cryptographic Primitives (Transparency Section)

> *(Adjust names if you want — this structure is what matters)*

- **Encryption Algorithm:** Mars Technology
- **Key Generation:** Cryptographically secure random bytes
- **Key Scope:** One-time use only
- **Key Storage:** Never persisted
- **IV / Nonce:** Unique per encryption
- **Integrity:** Enforced (tamper = destroy)
- **Password Derivation:** ❌ Not used
- **Key Recovery:** ❌ Impossible by design

> No master keys.  
> No backdoors.  
> No server-side decryption.

---

## 🏗️ High-Level Architecture

```

┌────────────┐
│   Client   │
└─────┬──────┘
│ Encrypt Request
▼
┌────────────┐
│  API Layer │
└─────┬──────┘
│ One-Time Key
▼
┌─────────────────┐
│ Encryption Core │
└─────┬───────────┘
│ Encrypted Artifact
▼
┌─────────────────┐
│ Ephemeral Store │  ← TTL enforced
└─────┬───────────┘
│ Download / Expiry
▼
┌─────────────────┐
│ Secure Destroy  │  ← Zero recovery
└─────────────────┘

```

---

## 🧨 Data Lifecycle (Zero-Trust Flow)

```

Create → Encrypt → Store (TTL) → Access Once → Destroy
↓
Expire Timer
↓
Destroy

```

**There is no state where plaintext is stored. Ever.**

---

## ⚙️ Deployment Notes (Minimal & Honest)

- Stateless backend
- Ephemeral storage only
- No persistent volumes
- No database dependency for secrets

> Restarting the server = destroys active data  
> This is a feature, not a bug.

---

## 🧪 Security Posture Summary

| Area | Status |
|----|----|
| Confidentiality | ✅ Strong |
| Integrity | ✅ Enforced |
| Availability | ⚠️ Best-effort |
| Recoverability | ❌ None |
| Persistence | ❌ Zero |
| Forgiveness | ❌ Zero |

---

## 🧠 Design Principle (Final Nail)

> **A secure system should fail closed — not leak open.**

This project **destroys data instead of risking exposure**.
