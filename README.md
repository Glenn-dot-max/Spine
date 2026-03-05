cd ~/Desktop/Dev/Spine/V1.1

cat > README.md << 'EOF'

# 📋 Spine CRM v1.1 - Guide de démarrage complet

## 🎯 Vue d'ensemble

**Spine CRM** est une application de gestion de la relation client (CRM) avec automatisation d'emails.

**Stack technique :**

- **Backend** : FastAPI (Python 3.9+)
- **Frontend** : React + TypeScript + Vite
- **Base de données** : PostgreSQL 15
- **OAuth** : Gmail & Outlook/Microsoft

---

## 📦 Prérequis

- **Python 3.9+** : https://www.python.org/downloads/
- **Node.js 18+** : https://nodejs.org/
- **Docker Desktop** : https://www.docker.com/products/docker-desktop/
- **Git** : https://git-scm.com/downloads/

---

## 🚀 Installation complète

### ÉTAPE 1 : Lancer PostgreSQL

\`\`\`bash
docker run --name postgres -e POSTGRES_USER=spine -e POSTGRES_PASSWORD=spinepassword -e POSTGRES_DB=spine -p 5432:5432 -d postgres:15
docker ps
\`\`\`

### ÉTAPE 2 : Backend

\`\`\`bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install "uvicorn[standard]"
pip install -r requirements.txt
\`\`\`

Créer \`backend/.env\` :
\`\`\`
DATABASE_URL=postgresql://spine:spinepassword@localhost:5432/spine
SECRET_KEY=changez-moi
GOOGLE_CLIENT_ID=votre-client-id
GOOGLE_CLIENT_SECRET=votre-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/gmail/callback
MICROSOFT_CLIENT_ID=votre-client-id
MICROSOFT_CLIENT_SECRET=votre-secret
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/oauth/outlook/callback
MICROSOFT_TENANT_ID=common
\`\`\`

Initialiser la DB :
\`\`\`bash
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
\`\`\`

### ÉTAPE 3 : Frontend

\`\`\`bash
cd ../frontend
npm install
\`\`\`

---

## ▶️ Démarrage quotidien

### 1. PostgreSQL

\`\`\`bash
docker start postgres
\`\`\`

### 2. Backend

\`\`\`bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
\`\`\`
✅ http://localhost:8000

### 3. Frontend

\`\`\`bash
cd frontend
npm run dev
\`\`\`
✅ http://localhost:5173

---

## 🗄️ PostgreSQL

\`\`\`bash
docker exec -it postgres psql -U spine -d spine
\`\`\`

\`\`\`sql
\\dt
SELECT \* FROM users;
\\q
\`\`\`

---

## 🔧 Configuration OAuth

### Gmail

1. https://console.cloud.google.com/
2. Créer projet "Spine CRM"
3. Activer Gmail API
4. OAuth Consent Screen → External
5. Scopes : openid, userinfo.email, gmail.readonly, gmail.send
6. Test users : votre email
7. Credentials → OAuth 2.0 → Redirect URI : http://localhost:8000/api/oauth/gmail/callback

### Outlook

1. https://portal.azure.com/
2. App registrations → New
3. Redirect URI : http://localhost:8000/api/oauth/outlook/callback
4. Client Secret → Copier la VALUE
5. API Permissions : Mail.Read, Mail.ReadWrite, Mail.Send, User.Read, offline_access
6. Grant admin consent

---

## 🐛 Dépannage

### Port 5432 occupé

\`\`\`bash
lsof -i :5432
brew services stop postgresql
\`\`\`

### Module psycopg manquant

\`\`\`bash
source venv/bin/activate
python -m uvicorn app.main:app --reload
\`\`\`

### OAuth redirect_uri_mismatch

Vérifier les redirect URIs :

- Gmail : http://localhost:8000/api/oauth/gmail/callback
- Outlook : http://localhost:8000/api/oauth/outlook/callback

---

## 📁 Structure

\`\`\`
Spine/V1.1/
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ ├── db.py
│ │ ├── models/
│ │ ├── api/
│ │ ├── routes/
│ │ └── services/
│ ├── .env
│ └── venv/
├── frontend/
│ ├── src/
│ └── node_modules/
└── README.md
\`\`\`

---

## 📊 État actuel

✅ Backend FastAPI  
✅ Frontend React  
✅ PostgreSQL  
✅ OAuth Gmail  
✅ OAuth Outlook

🚧 À faire :

- Auth JWT
- Envoi emails
- CRUD prospects
- Automatisation

---

## 👨‍💻 Développeur

Glenn Duval  
📧 glenn_duval@outlook.com

---

## 📅 Changelog

**2026-03-02** - OAuth Gmail/Outlook ✅

**À venir** - Envoi emails, prospects

---

🎉 Bon développement ! 🚀
EOF

echo "✅ README.md créé !"
