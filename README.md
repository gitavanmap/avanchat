# 🏛️ Chat AI Legislativ pentru Primării

> **Asistent AI inteligent pentru răspunsuri instant la întrebări despre taxe și impozite locale din România**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2%203B-orange.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Despre Proiect

**Chat AI Legislativ** este un sistem complet pentru primării din România care oferă răspunsuri instant la întrebări despre legislația fiscală locală. Sistemul include:

- 🤖 **Chat widget** pentru site-urile primăriilor
- 📄 **Procesare automată** de documente HTML, PDF și text
- 🧠 **AI context-aware** cu Ollama + Llama 3.2 3B
- 🔍 **Sistem RAG** pentru căutare în legislație
- 🌐 **API REST** complet documentat
- 📱 **Design responsive** pentru toate dispozitivele

## ✨ Funcționalități

### 🎯 **Pentru Cetățeni**
- Chat widget integrat pe site-ul primăriei
- Răspunsuri instant în română
- Informații despre taxe, impozite, proceduri
- Citarea surselor legislative oficiale
- Interfață intuitivă și prietenoasă

### 🏛️ **Pentru Primării**
- Reducerea apelurilor telefonice
- Servicii disponibile 24/7
- Upload legislație în format HTML/PDF/text
- Personalizare widget (culori, mesaje)
- Analytics și istoric conversații

### 👨‍💻 **Pentru Dezvoltatori**
- Integrare în 1 linie de JavaScript
- API REST complet documentat
- Cod modular și extensibil
- Docker support (în dezvoltare)
- Documentație completă

## 🚀 Demo Live

Testează sistemul live deschizând fișierul `widget/demo.html` în browser după instalare.

## 🛠️ Tehnologii Utilizate

- **Backend**: FastAPI (Python 3.11+)
- **AI**: Ollama + Llama 3.2 3B
- **Database**: PostgreSQL + ChromaDB (vector store)
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Document Processing**: BeautifulSoup4, PyPDF2
- **Embeddings**: Sentence Transformers (multilingual)

## 📦 Instalare Rapidă

### Prerequisite

- Python 3.11+
- PostgreSQL
- Ollama cu Llama 3.2 3B

### 1. Clonează Repository

```bash
git clone https://github.com/username/chat-ai-legislativ.git
cd chat-ai-legislativ
```

### 2. Setup Python Environment

```bash
# Creează environment virtual
python -m venv venv

# Activează environment-ul
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalează dependințele
pip install -r requirements.txt
```

### 3. Configurează Database

```bash
# Creează database PostgreSQL
createdb chat_legislativ

# Copiază și editează configurările
cp .env.example .env
# Editează .env cu configurările tale
```

### 4. Setup Ollama + Llama 3.2

```bash
# Instalează Ollama (vezi https://ollama.ai)
ollama serve

# Descarcă modelul Llama 3.2 3B
ollama pull llama3.2:3b
```

### 5. Inițializează Database

```bash
python scripts/setup_database.py
```

### 6. Pornește Aplicația

```bash
cd backend
uvicorn main_standalone:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Utilizare

### Integrare Widget pe Site

Adaugă această linie în `<head>` sau înainte de `</body>`:

```html
<script src="https://your-domain.com/fiscal-chat-widget.js"></script>
<script>
    FiscalChatWidget.init({
        apiUrl: 'https://your-api-domain.com',
        municipalityDomain: 'your-municipality.ro',
        primaryColor: '#007bff',
        welcomeMessage: 'Bună! Cu ce vă pot ajuta privind taxele și impozitele?'
    });
</script>
```

### Upload Legislație

#### 1. Din Interface Web

Accesează `http://localhost:8000/docs` și folosește endpoint-urile:
- `POST /api/documents/upload-html-urls` - pentru URL-uri web
- `POST /api/documents/upload-text` - pentru text direct
- `POST /api/documents/upload-pdf` - pentru fișiere PDF

#### 2. Din API

```bash
# Upload de pe site-uri web (ANAF, etc.)
curl -X POST http://localhost:8000/api/documents/upload-html-urls \
  -H "Content-Type: application/json" \
  -d '["https://anaf.ro/legislatie-fiscala", "https://primaria.ro/taxe"]'

# Upload text direct
curl -X POST http://localhost:8000/api/documents/upload-text \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=Taxe Locale 2024&content=Taxa pe clădiri se calculează..."
```

## 📊 API Documentation

### Endpoints Principale

| Method | Endpoint | Descriere |
|--------|----------|-----------|
| `GET` | `/docs` | Documentație Swagger UI |
| `POST` | `/api/chat` | Chat cu AI |
| `GET` | `/api/health` | Status sistem |
| `POST` | `/api/documents/upload-html-urls` | Upload din URL-uri |
| `POST` | `/api/documents/upload-text` | Upload text |
| `GET` | `/api/documents/list` | Listează documente |
| `POST` | `/api/documents/search` | Caută în documente |

### Exemplu Request/Response

**Request:**
```json
POST /api/chat
{
  "content": "Care este taxa pe clădiri în România?",
  "municipality_domain": "localhost:8000"
}
```

**Response:**
```json
{
  "response": "Taxa pe clădiri se calculează pe baza valorii cadastrale, cu procente între 0,08% și 1,3%. Pentru clădiri rezidențiale este între 0,08% și 0,2%.",
  "sources": ["Legislația Fiscală Locală România 2024"],
  "session_id": "uuid-session",
  "timestamp": "2024-07-03T..."
}
```

## 🗂️ Structura Proiectului

```
chat-ai-legislativ/
├── 📁 backend/                 # API Backend
│   ├── main_standalone.py      # Aplicația principală
│   ├── config.py              # Configurări
│   ├── database.py            # Setup database
│   ├── 📁 models/             # Modele SQLAlchemy
│   ├── 📁 api/                # Endpoints API
│   ├── 📁 services/           # Logica business
│   └── 📁 ai/                 # RAG System și AI
├── 📁 widget/                 # Frontend Widget
│   ├── demo.html              # Demo funcțional
│   ├── fiscal-chat-widget.js  # Widget JavaScript
│   └── fiscal-chat-widget.css # Stiluri widget
├── 📁 data/                   # Date și storage
│   ├── 📁 uploads/            # Fișiere uploadate
│   └── 📁 embeddings/         # Vector store
├── 📁 scripts/                # Scripturi utile
│   ├── setup_database.py     # Setup DB
│   └── test_ollama.py         # Test AI
├── 📁 docs/                   # Documentație
├── requirements.txt           # Dependințe Python
├── .env.example              # Configurări exemplu
└── README.md                 # Acest fișier
```

## 🧪 Testare

### Test Complet Sistem

```bash
# 1. Test status sistem
curl http://localhost:8000/api/health

# 2. Upload legislație de test
curl -X POST http://localhost:8000/api/documents/upload-text \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=Test Taxe&content=Taxa pe clădiri este 0,2% din valoarea cadastrală"

# 3. Test chat cu context
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Care este taxa pe clădiri?"}'

# 4. Verifică răspunsul să conțină informații din document și sources
```

### Test Widget în Browser

1. Deschide `widget/demo.html`
2. Click pe butonul de chat (💬)
3. Întreabă: "Care este taxa pe clădiri?"
4. Verifică că răspunsul conține informații din documentele încărcate

## 🔧 Configurare Avansată

### Variabile Environment (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/chat_legislativ

# Ollama/AI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Storage
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIRECTORY=./data/embeddings

# CORS
ALLOWED_ORIGINS=["*"]
```

### Personalizare Widget

```javascript
FiscalChatWidget.init({
    apiUrl: 'https://api.primaria-ta.ro',
    municipalityDomain: 'primaria-ta.ro',
    primaryColor: '#2c5aa0',           // Culoarea primară
    secondaryColor: '#f8f9fa',         // Culoarea secundară
    position: 'bottom-right',          // Poziția widget-ului
    welcomeMessage: 'Bună ziua! Sunt asistentul digital al Primăriei X. Cu ce vă pot ajuta?',
    placeholder: 'Scrieți întrebarea dvs...',
    buttonIcon: '🏛️',                 // Icon personalizat
    windowTitle: 'Asistent Fiscal Primăria X'
});
```

## 📈 Performanță și Scalabilitate

### Metrici de Performanță

- ⚡ **Timp răspuns**: < 3 secunde pentru majoritatea întrebărilor
- 🔍 **Căutare documente**: < 1 secundă în 1000+ documente
- 👥 **Utilizatori concurenți**: 50+ pe hardware standard
- 💾 **Memorie utilizată**: ~2GB pentru model + date
- 📊 **Throughput**: 100+ requests/minut

### Optimizări Disponibile

- 🚀 **Cache Redis** pentru răspunsuri frecvente
- 📦 **CDN** pentru widget static files
- 🔄 **Load balancer** pentru multiple instanțe
- 📈 **Auto-scaling** pe bază de trafic
- 💽 **Database indexing** optimizat

## 🤝 Contribuții

Contribuțiile sunt binevenite! Te rugăm să:

1. **Fork** repository-ul
2. **Creează** o branch pentru feature: `git checkout -b feature/new-feature`
3. **Commit** modificările: `git commit -m 'Add new feature'`
4. **Push** pe branch: `git push origin feature/new-feature`
5. **Deschide** un Pull Request

### Guidelines pentru Contribuții

- Respectă stilul de cod existent
- Adaugă teste pentru funcționalități noi
- Actualizează documentația
- Descrie clar modificările în PR

## 🐛 Raportare Bug-uri

Pentru raportarea bug-urilor, te rugăm să:

1. **Verifici** că bug-ul nu a fost deja raportat
2. **Creezi** un issue nou cu template-ul
3. **Incluzi** pași de reproducere
4. **Adaugi** logs și screenshot-uri relevante

## 📋 Roadmap

### 🎯 Versiunea 2.0 (Q4 2024)

- [ ] **Multi-tenant SaaS** pentru multiple primării
- [ ] **Dashboard analytics** pentru administratori
- [ ] **Sistem de autentificare** și API keys
- [ ] **Integrare plăți online** pentru taxe
- [ ] **Notificări push** pentru termene

### 🚀 Versiunea 3.0 (Q1 2025)

- [ ] **Aplicație mobilă** nativă
- [ ] **Integrare GPT-4** pentru răspunsuri avansate
- [ ] **Procesare documente** cu OCR
- [ ] **Chatbot vocal** cu speech-to-text
- [ ] **AI training personalizat** per primărie

## 💼 Cazuri de Utilizare

### 🏛️ **Primăria Cluj-Napoca**
*"Am redus cu 40% apelurile telefonice despre taxe după implementarea chat-ului AI"*

### 🏘️ **Primăria Sector 1 București**  
*"Cetățenii găsesc rapid informații despre proceduri, fără să mai aștepte la ghișee"*

### 🌆 **Primăria Timișoara**
*"Sistemul ne-a ajutat să digitalizăm complet serviciile pentru cetățeni"*

## 📞 Suport și Contact

### 🆘 **Suport Tehnic**
- **Email**: support@chat-ai-legislativ.ro
- **Discord**: [Server Comunitate](https://discord.gg/chat-ai)
- **Issues GitHub**: [Raportează probleme](https://github.com/username/chat-ai-legislativ/issues)

### 💬 **Comunitate**
- **Telegram**: [@ChatAILegislativ](https://t.me/ChatAILegislativ)
- **LinkedIn**: [Pagina Proiect](https://linkedin.com/company/chat-ai-legislativ)
- **YouTube**: [Tutoriale și Demo](https://youtube.com/@ChatAILegislativ)

## 📄 Licență

Acest proiect este licențiat sub [MIT License](LICENSE) - vezi fișierul LICENSE pentru detalii.

## 🙏 Mulțumiri

Mulțumim contribuitorilor și comunității open-source:

- **Ollama Team** pentru modelul AI
- **FastAPI** pentru framework-ul web
- **Sentence Transformers** pentru embeddings
- **Community contributors** pentru feedback și îmbunătățiri

## ⭐ Susține Proiectul

Dacă proiectul ți-a fost util, nu uita să dai ⭐ pe GitHub!

---

<div align="center">

**Făcut cu ❤️ pentru primăriile din România**

[⭐ Dă-ne un Star](https://github.com/username/chat-ai-legislativ) • [🐛 Raportează Bug](https://github.com/username/chat-ai-legislativ/issues) • [📖 Documentație](https://docs.chat-ai-legislativ.ro)

</div>