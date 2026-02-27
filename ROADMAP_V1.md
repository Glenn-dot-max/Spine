# Spine V1.0 — Roadmap (beta sales reps)

Objectif V1 : Campagnes (salons) → import prospects → ingestion catalogue scanné (OCR async) → sélection intérêts produits → composition + envoi Outlook (Microsoft Graph send-only) → suivi pipeline (Oven/Fridge/Trash) avec classement manuel des réponses.

## Principes

- Multi-tenant Microsoft OAuth (OIDC) + tokens internes (JWT)
- Données scoping **owner-only** : une campagne n’est visible que par son créateur
- Asynchrone via **RQ + Redis** : OCR jobs + envoi outbox
- Envoi email via **Microsoft Graph** (pas de SMTP)
- V1 : pas de lecture de mailbox, pas de détection automatique des réponses

---

## Milestone 0 — Repo & infra (1–2 jours)

- [ ] Backend FastAPI initial (`/health`)
- [ ] Postgres + Alembic (migration init)
- [ ] Redis (pour RQ)
- [ ] CI minimal (lint + tests)

**Livrable :** projet bootstrappé, migrations ok, healthcheck ok.

---

## Milestone 1 — Auth Microsoft (multi-tenant) + Users (4–6 jours)

- [ ] Modèles DB: `users`, `oauth_accounts`
- [ ] OAuth Microsoft (Authorization Code + PKCE)
- [ ] Endpoint: `GET /auth/microsoft/login` (URL d’auth)
- [ ] Endpoint: `GET /auth/microsoft/callback` (création user + liaison oauth)
- [ ] JWT interne + middleware auth
- [ ] Endpoint protégé: `GET /me`
- [ ] Tests: routes protégées + génération/validation JWT

**Livrable :** sales reps peuvent se connecter (login only: `openid profile email`).

---

## Milestone 2 — Core CRM : Distributors + Campaigns (owner-only) (3–5 jours)

- [ ] Tables: `distributors`, `campaigns(owner_user_id)`
- [ ] CRUD distributors (owner)
- [ ] CRUD campaigns (owner)
- [ ] Filtres/pagination simples

**Livrable :** création d’une campagne (évènement + distributeur + lieu/date).

---

## Milestone 3 — Prospects + Import + Pipeline stages (4–6 jours)

- [ ] Tables: `prospects`, `campaign_prospects`
- [ ] Import CSV prospects dans une campaign (idempotent: éviter doublons)
- [ ] Champs contact requis (email, prénom/nom, société…)
- [ ] Stages: `waiting_room`, `oven`, `fridge`, `trash`
- [ ] Endpoints: listing par stage + update stage manuel (OUI/NON/Ghost/Trash)
- [ ] Audit log minimal (qui a changé quoi, quand) (option mais recommandé)

**Livrable :** pipeline exploitable par campagne.

---

## Milestone 4 — Outbox (fiabilisation) (3–5 jours)

- [ ] Tables: `outbox_emails`, `email_send_logs`
- [ ] Statuts: `draft`, `ready`, `sending`, `sent`, `failed`
- [ ] Idempotency key (anti double-send)
- [ ] Worker RQ: traitement outbox + retries simples
- [ ] Endpoint: créer un outbox_email (draft/ready)

**Livrable :** envoi “industrialisé” (même avant Graph).

---

## Milestone 5 — Microsoft Graph send-only (4–6 jours)

- [ ] Consent “send-only” (scopes `Mail.Send offline_access`)
- [ ] Stockage refresh token + expires_at (sécurisation à définir)
- [ ] Service Graph: `POST /me/sendMail`
- [ ] Worker outbox: envoi Graph + log provider_message_id
- [ ] Gestion erreurs: invalid recipient, throttling, token refresh

**Livrable :** envoi Outlook stable via Graph, traçable.

---

## Milestone 6 — Catalogue salon (PDF scanné) + OCR async + Produits (5–8 jours)

- [ ] Tables: `catalogs`, `ingestion_jobs`, `products`, `product_assets`
- [ ] Upload PDF catalogue rattaché à campaign
- [ ] Job OCR async (Google Document AI / Vision) → texte
- [ ] Extraction IA “one-shot” → JSON strict (validation) → staging
- [ ] Review/publish: endpoint pour valider & importer les produits
- [ ] Listing produits + recherche simple

**Livrable :** catalogue exploitable sous forme de produits en DB.

---

## Milestone 7 — Intérêts produits + Mixer preview (4–6 jours)

- [ ] Table: `prospect_product_interest` (scopée campaign)
- [ ] UI/API: sélectionner produits d’intérêt + notes
- [ ] Templates email simples (subject/body)
- [ ] Génération `catalog_block` (HTML + text) depuis intérêts
- [ ] Endpoint: `POST /mixer/preview` (subject + body final)

**Livrable :** emails personnalisés (template + blocs produits) prêts à envoyer.

---

## Milestone 8 — Beta hardening (optionnel, 3–5 jours)

- [ ] Exports CSV (Oven/Fridge)
- [ ] Observabilité (logs structurés, erreurs)
- [ ] Permissions fines (si besoin plus tard)
- [ ] Seed data + scripts d’import

**Livrable :** version testeurs stable + supportable.

---

## Estimation globale

- MVP testable (Milestones 0 → 7) : ~ **4–6 semaines**
- Beta durcie (avec Milestone 8) : ~ **5–7 semaines**
