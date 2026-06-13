# ⚖️ Sistema Legal CO

**Sistema integral de gestión legal con IA para abogados colombianos.**

Plataforma todo-en-uno que combina inteligencia artificial, procesamiento de documentos y herramientas jurídicas especializadas para optimizar el trabajo de despachos de abogados en Colombia. Todos los módulos implementados y funcionando.

---

## 🚀 Características

### Módulos del Sistema

| Módulo | Descripción | API | Tests |
|--------|-------------|-----|-------|
| 🔐 **Autenticación** | Registro, login JWT con roles (admin/abogado/asistente), refresh tokens | 4 endpoints | ✅ |
| 🗂️ **Gestión de Casos** | CRUD de expedientes con filtros, búsqueda y permisos por rol | 5 endpoints | ✅ |
| 💬 **Chat Legal IA** | Chat interactivo REST + WebSocket con orquestación de 10+ módulos | 3 endpoints | ✅ |
| 📄 **Documentos** | Carga multi-archivo drag & drop, procesamiento PDF/DOCX/OCR | 6 endpoints | ✅ |
| 🖊️ **Redacción Jurídica** | Generación de demandas, tutelas, recursos, derechos de petición vía LLM + Jinja2 | 5 endpoints | ✅ |
| 🔍 **Extracción de Metadatos** | NER legal (radicado, juzgado, partes, fechas, normas, cuantía, tipo proceso) | — | ✅ |
| 🎤 **Análisis de Testimonios** | Extracción de declaraciones, detección de contradicciones, resumen ejecutivo | — | ✅ |
| 🔎 **Auditoría Legal** | 13 reglas de auditoría (CGP, CPACA, CPP) + análisis LLM, hallazgos por criticidad | 3 endpoints | ✅ |
| ⚖️ **Jurisprudencia** | Búsqueda en 4 fuentes oficiales con fallbacks + RAG con ChromaDB | 5 endpoints | ✅ |
| 📊 **Diagramas** | Diagramas Mermaid (timeline, flowchart, graph) con exportación PNG/SVG | 2 endpoints | ✅ |
| ⚔️ **Análisis Adversarial** | Perspectiva juez y contra-parte sobre el mismo documento | 4 endpoints | ✅ |
| ⏱️ **Calculadora** | 22 términos procesales (CGP, CPACA, CPP) con alertas visuales | 3 endpoints | ✅ |
| 🧠 **Auto Timeline** | Cronología automática desde metadatos y texto del caso | 2 endpoints | ✅ |
| ✅ **Red Team** | Verificación anti-alucinaciones con score 0-100 | — | ✅ |

**Total: 139 tests pasando** (0 fallos, 1 skip por integración)

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.12+ / FastAPI |
| **Frontend** | React 19 + Vite + Tailwind CSS + TypeScript |
| **Estado** | Zustand 5 con persist |
| **LLM** | LiteLLM → Ollama / Gemini / Claude / OpenAI / OpenRouter |
| **Vector DB** | ChromaDB (embeddings locales) |
| **DB** | SQLite (dev) / PostgreSQL (prod) + SQLAlchemy 2.0 |
| **Migraciones** | Alembic |
| **PDF** | PyMuPDF + pdfplumber |
| **OCR** | PaddleOCR (optimizado español) |
| **Word** | python-docx + Jinja2 |
| **PDF Export** | WeasyPrint con CSS NTC 1486 |
| **Autenticación** | JWT (access + refresh) + bcrypt |
| **Testing** | pytest + pytest-asyncio |
| **Contenedores** | Docker + docker-compose (dev y prod) |

---

## 📋 Requisitos

- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose** (opcional, recomendado)

---

## 🚀 Inicio Rápido

### Opción 1: Docker (recomendado)

```bash
# Clonar
git clone <repo-url>
cd sistema-legal

# Iniciar todo (backend + frontend)
docker-compose up --build

# Frontend: http://localhost:5173
# API:      http://localhost:8000
# Docs API: http://localhost:8000/docs
```

### Opción 2: Desarrollo manual

#### Backend

```bash
cd backend
cp .env.example .env
# Editar .env si es necesario

python -m venv venv
# Linux/Mac: source venv/bin/activate
# Windows:   venv\Scripts\activate
pip install -r requirements.txt

# Iniciar servidor
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev

# Abrir http://localhost:5173
```

### Variables de Entorno (`.env`)

```env
# Base de datos (SQLite dev / PostgreSQL prod)
DATABASE_URL=sqlite:///./sistema_legal.db
# DATABASE_URL=postgresql://user:password@localhost:5432/sistema_legal

# LLM Provider (ollama, gemini, claude, openai, openrouter)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
# GEMINI_API_KEY=...
# CLAUDE_API_KEY=...
# OPENAI_API_KEY=...
# OPENROUTER_API_KEY=...

# Autenticación JWT
JWT_SECRET=cambiar_en_produccion
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Producción

```bash
docker-compose -f docker-compose.production.yml up --build -d
```

---

## 🔧 Arquitectura

```
Frontend (React 19 + Vite + Tailwind)
       ↕ REST + WebSocket
       ↕ JWT en cada request
FastAPI (Python)
  └─ Auth Middleware (JWT + roles)
  └─ Orchestrator → 10+ módulos
       ├─ Cases          → SQLAlchemy ORM
       ├─ Drafting       → Jinja2 + LiteLLM → DOCX / PDF
       ├─ Extraction     → PyMuPDF + PaddleOCR → JSON
       ├─ Testimony      → Análisis de declaraciones
       ├─ Audit          → Reglas + LLM
       ├─ Jurisprudence  → httpx + ChromaDB RAG
       ├─ Diagram        → Mermaid generator
       ├─ Adversarial    → juez / contra-parte
       ├─ Calculator     → Términos procesales
       ├─ Timeline       → Cronología automática
       └─ Red Team       → Anti-alucinaciones
  └─ LiteLLM (Ollama / Gemini / Claude / OpenAI / OpenRouter)
  └─ ChromaDB + SQLite (dev) / PostgreSQL (prod)
```

---

## 🧪 Pruebas

```bash
# Backend — todos los tests (139)
cd backend
pytest tests/ -v

# Solo un módulo
pytest tests/test_audit.py -v

# Frontend — typecheck
cd frontend
npx tsc --noEmit

# Build producción
npm run build
```

---

## 📚 Documentación de API

Una vez iniciado el backend:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints Principales

```
POST   /api/auth/register         Registrar usuario
POST   /api/auth/login            Iniciar sesión
POST   /api/auth/refresh          Renovar token JWT
GET    /api/auth/me               Perfil del usuario actual

POST   /api/cases/                Crear caso
GET    /api/cases/                Listar casos (con filtros)
GET    /api/cases/{id}            Detalle del caso
PUT    /api/cases/{id}            Actualizar caso
DELETE /api/cases/{id}            Eliminar caso (admin)

POST   /api/chat/message          Enviar mensaje al chat IA
WS     /api/chat/ws               WebSocket chat en tiempo real
GET    /api/chat/history/{id}     Historial de conversación

POST   /api/documents/upload/{case_id}          Subir archivo
POST   /api/documents/upload-multiple/{case_id}  Subir múltiples
GET    /api/documents/{id}                       Ver metadata
GET    /api/documents/{id}/download              Descargar
GET    /api/documents/{id}/text                  Texto extraído
DELETE /api/documents/{id}                       Eliminar

POST   /api/export/generate      Generar documento legal
POST   /api/export/docx          Exportar a Word (NTC 1486)
POST   /api/export/pdf           Exportar a PDF
GET    /api/export/versions/{case_id}    Versiones guardadas
GET    /api/export/versions/{id}/download Descargar versión

POST   /api/audit/case/{case_id}  Auditar caso completo
POST   /api/audit/document        Auditar texto
GET    /api/audit/reglas          Listar reglas de auditoría

POST   /api/jurisprudence/search        Buscar en fuente específica
POST   /api/jurisprudence/search/all     Buscar en todas las fuentes
POST   /api/jurisprudence/semantic       Búsqueda semántica (RAG)
GET    /api/jurisprudence/sources        Fuentes disponibles
POST   /api/jurisprudence/cache/clear    Limpiar caché (admin)

POST   /api/diagram/generate            Generar diagrama
POST   /api/diagram/from-case/{case_id}  Desde datos del caso

POST   /api/calculator/calcular          Calcular término
POST   /api/calculator/alertas/{case_id} Alertas del caso
GET    /api/calculator/lista             Listar términos disponibles

POST   /api/timeline/from-case/{case_id}  Timeline del caso
POST   /api/timeline/from-text            Timeline desde texto

POST   /api/adversarial/analyze/{case_id}       Analizar desde perspectiva
POST   /api/adversarial/analyze/text             Analizar texto
POST   /api/adversarial/analyze/both/{case_id}  Análisis dual
GET    /api/adversarial/perspectives             Perspectivas disponibles
```

---

## 🔐 Roles de Usuario

| Rol | Permisos |
|-----|----------|
| **admin** | Acceso total, eliminar casos, gestionar usuarios, limpiar caché |
| **abogado** | CRUD casos propios, redacción jurídica, análisis completo, exportación |
| **asistente** | Ver casos asignados, chat básico, subir documentos |

---

## 📁 Estructura del Proyecto

```
sistema-legal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point (48 routes)
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── api/routes/          # 11 routers (auth, cases, chat...)
│   │   ├── core/                # LLM, JWT, orchestrator, memory
│   │   ├── models/              # SQLAlchemy models (7 entidades)
│   │   ├── modules/             # 10 módulos funcionales
│   │   └── db/                  # database.py + vector_store.py
│   ├── tests/                   # 139 tests (pytest)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Auth, Cases, Chat, Documents, Diagram, UI
│   │   ├── hooks/               # useAuth (Zustand), useChat
│   │   ├── services/            # Axios API client con refresh automático
│   │   └── types/               # TypeScript interfaces
│   └── package.json
├── data/                        # Volumen persistente Docker
│   ├── uploads/
│   └── jurisprudence/
├── docker-compose.yml           # Desarrollo (hot-reload)
├── docker-compose.production.yml
└── README.md
```

---

## 🏗️ Convenios de Desarrollo

### Backend
- **Python 3.12+** con type hints
- **FastAPI** con routers por módulo
- **SQLAlchemy 2.0** async session management
- **Alembic** para migraciones automáticas
- **pytest** con fixtures, parametrize, async support

### Frontend
- **React 19** con named imports (nunca `import React`)
- **Zustand 5** con persist para estado global
- **Tailwind CSS** con dark mode
- **Error boundaries** para manejo de errores
- **Skeleton screens** para estados de carga

---

## 📄 Licencia

Privada — todos los derechos reservados.

---

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/)
- [LiteLLM](https://litellm.ai/)
- [ChromaDB](https://www.trychroma.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
- [CodeGraph](https://github.com/colbymchenry/codegraph)
