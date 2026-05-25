# SPINE V1 — CONTEXTE COMPLET POUR IA DE CODING

> Ce fichier est le contexte de référence du projet Spine V1.
> Il est destiné à l'IA de coding (Cursor / Copilot / Continue) pour
> comprendre l'architecture, l'état d'avancement, et les priorités.
> Dernière mise à jour : juin 2026

---

## 🧭 C'est quoi Spine ?

Spine est un CRM SaaS B2B ciblant les sales reps de la food distribution en Amérique du Nord.
Il permet de gérer un portefeuille de comptes, d'automatiser les relances, de traiter les emails
avec assistance IA, et de lancer des campagnes de mailing multi-templates.

**Produit :** Starter $49/user/mois — V1 en cours de développement
**Structure :** LDM SASU (France) — revenus Stripe USD → virement EUR
**Développeur :** Glenn Duval (solo) + review freelance toutes les 2 semaines
**Objectif :** V1 déployée et testable à l'retour en France — octobre 2026

---

## 🏗️ Stack technique

| Couche            | Technologie                                                    | Version cible |
| ----------------- | -------------------------------------------------------------- | ------------- |
| Backend           | FastAPI (Python)                                               | 3.11+         |
| ORM / Migrations  | SQLAlchemy + Alembic                                           | —             |
| Base de données   | PostgreSQL                                                     | 16            |
| Cache             | Redis                                                          | 7             |
| Anonymisation     | presidio-analyzer + presidio-anonymizer + spaCy en_core_web_lg | —             |
| IA                | Anthropic Claude Haiku (claude-haiku-4-5)                      | —             |
| OAuth email       | Gmail API (google-auth) + Microsoft Graph (msal)               | —             |
| Chiffrement       | cryptography (Fernet AES-256)                                  | —             |
| Tâches background | APScheduler                                                    | —             |
| Frontend          | React 18 + Vite + Tailwind CSS + shadcn/ui                     | —             |
| Infra cible       | Hetzner VPS CX22 — Docker Compose + Nginx                      | —             |
| CI/CD             | GitHub Actions                                                 | —             |
| Monitoring        | Sentry (free tier) + Uptimerobot                               | —             |
| Paiements         | Stripe (abonnements récurrents)                                | —             |

---

## 📁 Structure du projet

```
spine/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings (env vars)
│   ├── database.py              # PostgreSQL connection + session
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── account.py
│   │   ├── contact.py
│   │   ├── account_rep.py
│   │   ├── crm_note.py
│   │   ├── email_sequence.py
│   │   ├── ride_along.py
│   │   ├── product.py
│   │   ├── distributor_catalog.py
│   │   ├── campaign.py
│   │   ├── oauth_token.py
│   │   ├── user_signature.py
│   │   └── token_usage.py
│   ├── routes/
│   │   ├── auth.py              # JWT login/register/refresh
│   │   ├── accounts.py          # CRM accounts CRUD
│   │   ├── contacts.py          # CRM contacts CRUD
│   │   ├── emails.py            # Email fetch + composer
│   │   ├── campaigns.py         # Campaign module
│   │   ├── catalogue.py         # Product upload + distributor catalogs
│   │   ├── ride_along.py        # Ride along module
│   │   ├── ai.py                # Haiku endpoints
│   │   ├── oauth.py             # Gmail + Outlook OAuth
│   │   ├── webhooks.py          # Stripe webhooks
│   │   └── settings.py          # User settings + signature
│   ├── services/
│   │   ├── anonymizer.py        # Pipeline Presidio
│   │   ├── haiku.py             # Appels Haiku (suggest, improve, note, campaign)
│   │   ├── gmail.py             # Gmail API wrapper
│   │   ├── outlook.py           # Microsoft Graph wrapper
│   │   ├── poller.py            # APScheduler — fetch emails toutes les 2h
│   │   ├── sender.py            # Envoi emails OAuth + throttling anti-spam
│   │   ├── catalogue_parser.py  # PDF + CSV parsing
│   │   ├── campaign_classifier.py # Classification contacts → templates
│   │   ├── corps_mail.py        # Templates email food distribution (EXISTANT)
│   │   ├── notifier.py          # Notifications email deep link
│   │   └── stripe_service.py    # Stripe customer + subscription
│   ├── security/
│   │   ├── jwt.py               # JWT access + refresh tokens
│   │   ├── encryption.py        # AES-256 Fernet
│   │   └── rate_limit.py        # Rate limiting login
│   ├── worker.py                # APScheduler entry point
│   ├── alembic/                 # Migrations DB
│   └── tests/                   # Tests unitaires + intégration
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Header.tsx
│   │   │   ├── crm/
│   │   │   │   ├── AccountCard.tsx
│   │   │   │   ├── AccountHeader.tsx
│   │   │   │   └── NoteTimeline.tsx
│   │   │   ├── email/
│   │   │   │   ├── EmailCard.tsx
│   │   │   │   ├── SuggestionPicker.tsx
│   │   │   │   └── TwoColumnLayout.tsx
│   │   │   ├── campaign/
│   │   │   │   ├── CsvUploader.tsx
│   │   │   │   ├── TemplatePreview.tsx
│   │   │   │   └── SpamScoreBadge.tsx
│   │   │   └── ui/              # shadcn/ui components
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── CRM.tsx
│   │   │   ├── AccountDetail.tsx
│   │   │   ├── EmailInbox.tsx
│   │   │   ├── Campaigns.tsx
│   │   │   ├── RideAlong.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/               # React Query hooks
│   │   ├── lib/                 # API client, utils
│   │   └── main.tsx
│   └── vite.config.ts
├── nginx/
│   └── conf.d/spine.conf
├── docker-compose.yml
├── .env.example
├── .github/
│   └── workflows/deploy.yml
└── SPINE_V1_CONTEXT.md          # CE FICHIER
```

---

## 🗄️ Base de données — Tables V1

### Tables principales et leur rôle

```
users                   Comptes sales reps (login, role, tier)
companies               Tenants Spine (1 company = 1 équipe)
accounts                Fiches entreprises CRM (chain_level, parent_account_id)
contacts                Contacts liés aux comptes
account_reps            Sales reps externes par distributeur (auto_cc)
crm_notes               Notes Haiku anonymisées (jamais de PII)
email_sequences         Séquences post-salon / post-ride along
ride_alongs             Journées de visite terrain
ride_along_visits       Fiches de visite par compte
products                Catalogue général (source supprimée après extraction)
distributor_catalogs    Sous-sélection catalogue par distributeur
distributor_catalog_items  Produits inclus dans un catalogue distributeur
campaigns               Campagnes de mailing
campaign_contacts       Contacts importés CSV
campaign_templates      Templates générés par segment (HTML)
campaign_emails         Drafts individuels (supprimés après envoi)
campaign_sends          Logs d'envoi (métadonnées uniquement)
campaign_replies        Réponses détectées (anonymisées)
campaign_attachments    PDF uploadés (TTL 30j, AES-256)
email_blacklist         Adresses blacklistées (SHA-256 — jamais en clair)
oauth_tokens            Tokens Gmail/Outlook (AES-256)
user_signatures         Signatures email (OAuth fetch + manuel)
token_usage             Consommation tokens Haiku par user/mois
stripe_customers        Mapping company → Stripe customer
stripe_subscriptions    Plan actif + statut
stripe_invoices         Historique factures
```

### Règle absolue multi-tenant

```python
# TOUJOURS filtrer par user_id sur chaque requête
# Sans exception — c'est la sécurité de base du produit

# ✅ Correct
SELECT * FROM accounts WHERE id = $1 AND user_id = $2

# ❌ Jamais
SELECT * FROM accounts WHERE id = $1
```

---

## 🔐 Sécurité — Règles non négociables

```
1. JAMAIS stocker un email brut en base PostgreSQL
   → Cache Redis TTL 1h uniquement, AES-256, purgé après traitement

2. JAMAIS envoyer de PII à l'API Anthropic
   → Anonymisation Presidio AVANT tout appel Haiku

3. TOUJOURS chiffrer les tokens OAuth avant écriture en base
   → AES-256 Fernet, clé dans ENCRYPTION_KEY (env var)

4. JAMAIS logger le contenu d'un email
   → Logger uniquement : email_id, user_id, nb_entités, statut

5. TOUJOURS vérifier user_id sur chaque requête SQL
   → Isolation multi-tenant stricte

6. Blacklist emails en SHA-256 uniquement
   → Jamais l'adresse en clair
```

---

## 🤖 Pipeline IA — Fonctionnement

```
Email brut (Gmail / Outlook)
        ↓
① Fetch OAuth → Redis cache TTL 1h (AES-256)
        ↓
② Anonymisation Presidio (LOCAL — ne quitte pas le serveur)
   Entités détectées : PERSON, EMAIL_ADDRESS, PHONE_NUMBER,
   ORGANIZATION, LOCATION, MONEY, DATE_TIME, URL
   Remplacées par : [PERSONNE], [EMAIL], [TÉLÉPHONE]...
        ↓
③ Détection métier (règles locales — pas d'IA)
   → segment, tone, intents, urgency
        ↓
④ Résumé structuré anonymisé → envoyé à Haiku
        ↓
⑤ Haiku génère (selon le mode) :
   - suggest_reply  : 3 options Directe / Relationnelle / Neutre
   - improve        : reformulation du mail rédigé par le user
   - generate_note  : JSON {summary, intents, sentiment, urgency, next_action}
   - campaign_email : email campagne avec contexte produit
        ↓
⑥ Note CRM stockée en PostgreSQL (anonymisée)
⑦ Cache Redis purgé immédiatement
```

### Modèle Haiku — Paramètres

```python
# Toujours utiliser claude-haiku-4-5
# max_tokens : 1024 pour notes, 1500 pour suggest_reply, 1000 pour campaign
# System prompt : voir services/haiku.py — food distribution context

MODEL = "claude-haiku-4-5"

# Quota tokens par tier (Redis incr par user_id + mois)
TOKEN_QUOTAS = {
    "starter":   500_000,
    "pro":     1_500_000,
    "assistant": 5_000_000,
}
```

---

## 📧 Pipeline email — Anti-spam

```python
# Règles d'envoi strictes — non modifiables par le user
SENDING_RULES = {
    "max_per_day":    50,    # limite Gmail safe
    "delay_between":  90,    # secondes entre chaque email
    "batch_size":     10,
    "batch_pause":    600,   # 10 min entre batches
    "max_per_domain": 3,
}

# Séquence campagne
# J0  → init_html()     (corps_mail.py)
# J+5 → relance_html(relance_no=1)  si pas de réponse
# J+14→ relance_html(relance_no=2)  si toujours pas de réponse
# Stop automatique si réponse détectée (poller OAuth)
# Blacklist automatique si bounce hard (SHA-256)
```

---

## 📦 Module campagnes — Classification contacts

```python
# 3 variables → template_key
def classify_contact(row: dict) -> str:
    structure = row.get("type_structure", "").lower()
    canal     = row.get("canal", "").lower()
    produit   = row.get("produit_interet", "").lower()

    # Tier
    if structure in ["industry", "industrie"]:  tier = "IND"
    elif structure in ["restaurant", "chain"]:  tier = "REST"
    elif structure == "foodservice":            tier = "FS"
    elif structure == "retail":                 tier = "RET"
    else:                                       tier = "GEN"

    # Canal
    if "trade show" in canal:  ctx = "TS"
    elif canal == "referral":  ctx = "REF"
    elif canal == "linkedin":  ctx = "LI"
    elif canal == "inbound":   ctx = "IN"
    else:                      ctx = "EM"

    # Produit
    if "mustard" in produit or "moutarde" in produit:    prod = "MUS"
    elif "balsamic" in produit or "balsamique" in produit: prod = "BAL"
    elif "vinegar" in produit or "vinaigre" in produit:  prod = "VIN"
    elif "crepes" in produit:                            prod = "CR"
    else:                                                prod = "ALL"

    return f"{tier}_{ctx}_{prod}"
    # Exemples : "IND_TS_MUS", "REST_REF_VIN", "RET_EM_BAL"
```

---

## ✅ État d'avancement V1 — Ce qui est FAIT

```
✅ Pipeline anonymisation Presidio (testé en local)
   → services/anonymizer.py — fonctionne sur emails complexes food distribution
   → spaCy en_core_web_lg installé et validé

✅ Intégration Haiku — suggest reply + improve
   → services/haiku.py (spine_v1_starter.py comme base)
   → System prompt food distribution calibré
   → 3 options de réponse (Directe / Relationnelle / Neutre)
   → Improve my email fonctionnel

✅ corps_mail.py — templates email food distribution
   → Personnalisation par type_structure, canal, produit_interet
   → init_html() + relance_html() opérationnels
   → Signature remplacée par <!-- SIGNATURE_PLACEHOLDER -->

✅ Tests pipeline complets en local
   → anonymize_email.py validé sur emails réels
   → spine_v1_starter.py testé end-to-end avec clé Anthropic
```

---

## ⏳ Ce qui reste à coder — Priorités V1

### 🔴 Bloquants (sans ça, pas de V1)

```
[ ] Auth JWT — login, register, refresh token, logout
    → routes/auth.py + security/jwt.py
    → Access token 15min + refresh token 7j
    → Rate limiting 5 tentatives/10min par IP

[ ] Modèles SQLAlchemy + migrations Alembic
    → Toutes les tables listées ci-dessus
    → user_id filtré sur chaque modèle

[ ] Chiffrement AES-256 tokens OAuth
    → security/encryption.py
    → Fernet.generate_key() → ENCRYPTION_KEY env var

[ ] OAuth Gmail
    → services/gmail.py
    → Scopes : gmail.readonly + gmail.send + gmail.settings.basic
    → Fetch emails, send, read signature

[ ] OAuth Outlook
    → services/outlook.py
    → Scopes : Mail.Read + Mail.Send + MailboxSettings.Read
    → Fallback saisie manuelle si signature non accessible

[ ] Poller OAuth (APScheduler)
    → worker.py + services/poller.py
    → Toutes les 2h — fetch nouveaux emails
    → Pipeline anonymisation → note CRM → purge cache

[ ] generate_note() — Haiku génère la note CRM
    → services/haiku.py — ajouter cette fonction
    → Output JSON : {summary, intents, sentiment, urgency, next_action}
    → Stockée en crm_notes (anonymisée)

[ ] store_note() + purge_cache()
    → Écriture PostgreSQL + suppression Redis post-traitement

[ ] CRM CRUD — accounts + contacts
    → routes/accounts.py + routes/contacts.py
    → Isolation user_id sur toutes les requêtes

[ ] Quota tokens Redis par user/mois
    → Vérification avant chaque appel Haiku
    → Blocage si dépassement

[ ] Notification email deep link
    → services/notifier.py
    → Template HTML avec contexte anonymisé
    → Lien vers app.spine.io/inbox

[ ] Envoi email OAuth + throttling
    → services/sender.py
    → SENDING_RULES ci-dessus
    → Blacklist SHA-256 check avant envoi

[ ] Auth JWT + Stripe abonnement
    → Vérifier statut subscription avant chaque requête
    → Bloquer si past_due ou canceled

[ ] Frontend React — écrans principaux
    → Dashboard, CRM liste + fiche, Email composer, Settings OAuth
```

### 🟡 Importants (V1 complète mais pas bloquants au lancement)

```
[ ] Séquences post-salon + post-ride along
[ ] Module ride along (création journée + fiches visites)
[ ] Upload catalogue PDF + CSV (pdfplumber + pandas)
[ ] Catalogues distributeurs (sous-sélection)
[ ] Module campagnes complet (étapes 1 à 5)
[ ] Pièces jointes PDF (upload TTL 30j + AES-256)
[ ] Signatures email (OAuth fetch + saisie manuelle)
[ ] Improve my email (endpoint FastAPI)
[ ] Chaîne distribution (chain_level + parent_account_id + account_reps)
[ ] Stripe webhooks (subscription lifecycle)
[ ] Frontend React — campagnes + ride along + catalogue
```

### 🟢 Post-V1 (ne pas toucher maintenant)

```
[ ] PWA / mobile
[ ] Version Pro (Sonnet, scoring comptes, proactif)
[ ] Version Assistant (Opus, next best action)
[ ] App native iOS
[ ] ZDR Anthropic (enterprise)
[ ] Audit CASA Google (>100 users)
```

---

## 🧪 Tests à implémenter

```python
# Priorité 1 — Pipeline anonymisation
# tests/test_anonymizer.py
# - 50+ emails réels food distribution
# - Vérifier qu'aucun PERSON / EMAIL / PHONE ne passe
# - Tester les cas limites (noms d'entreprises courts, prix sans $)

# Priorité 2 — Isolation multi-tenant
# tests/test_multitenancy.py
# - User A ne peut pas accéder aux données de User B
# - Tester chaque endpoint GET/PATCH/DELETE

# Priorité 3 — Quota tokens
# tests/test_quota.py
# - Vérifier le blocage au-delà du quota
# - Vérifier le reset en fin de mois

# Priorité 4 — Throttling anti-spam
# tests/test_sender.py
# - Vérifier le délai de 90s entre envois
# - Vérifier la blacklist SHA-256
```

---

## 🌍 Variables d'environnement requises

```bash
# .env.example — copier en .env et remplir

# API Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Base de données
DATABASE_URL=postgresql://spine:password@localhost:5432/spine

# Cache
REDIS_URL=redis://:password@localhost:6379

# Sécurité
ENCRYPTION_KEY=          # Fernet.generate_key().decode()
JWT_SECRET=              # secrets.token_hex(32)
JWT_ACCESS_EXPIRE=900    # 15 minutes en secondes
JWT_REFRESH_EXPIRE=604800 # 7 jours en secondes

# OAuth Gmail
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=https://api.spine.io/oauth/gmail/callback

# OAuth Outlook
OUTLOOK_CLIENT_ID=
OUTLOOK_CLIENT_SECRET=
OUTLOOK_REDIRECT_URI=https://api.spine.io/oauth/outlook/callback
OUTLOOK_TENANT_ID=common

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_TEAM=price_...

# App
SPINE_BASE_URL=https://app.spine.io
ENVIRONMENT=development
SENTRY_DSN=
VERSION=1.0.0
```

---

## 💡 Questions pour l'IA de coding

En lisant ce fichier, voici ce que j'attends de toi :

**1. Audit de l'existant**
Regarde le code déjà écrit (anonymizer.py, spine_v1_starter.py, corps_mail.py).
Dis-moi ce qui est propre, ce qui doit être refactorisé, et ce qui manque pour être production-ready.

**2. Priorisation**
Selon toi, dans quel ordre implémenter les bloquants listés ci-dessus ?
Y a-t-il des dépendances entre eux que je n'ai pas vues ?

**3. Sécurité**
Y a-t-il des failles de sécurité dans l'architecture décrite ?
Notamment sur le pipeline OAuth, le cache Redis, et l'isolation multi-tenant.

**4. Cohérence technique**
La stack choisie (FastAPI + SQLAlchemy + Redis + Presidio + Haiku) est-elle cohérente ?
Y a-t-il des choix techniques qui vont me créer des problèmes plus tard ?

**5. Ce que tu ferais différemment**
Si tu partais de zéro sur ce projet, qu'est-ce que tu changerais dans l'architecture ?

---

## 📅 Planning sprints

```
Sprint 1  Juin S1   Fondations : FastAPI + PostgreSQL + Redis + Auth JWT
Sprint 2  Juin S2   OAuth Gmail + Outlook + Pipeline anonymisation
Sprint 3  Juil S1   Haiku (generate_note) + CRM CRUD + Poller
Sprint 4  Juil S2   Email composer + Séquences + Ride along
Sprint 5  Août S1   Catalogues + Campagnes étapes 1-3
Sprint 6  Août S2   Campagnes étapes 4-5 + Anti-spam + PJ + Signatures
Sprint 7  Septembre Frontend React + Freelance : nettoyage + sécurisation + déploiement

Review freelance : tous les 15 jours (fin de chaque sprint)
Livraison V1 : octobre 2026 (retour en France)
Premier client : janvier 2027 (White Toque Team $349)
```
