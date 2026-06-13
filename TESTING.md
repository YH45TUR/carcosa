# 🧪 Sistema Legal CO — Guia de Pruebas

> **Actualizado:** 13 de junio de 2026
> **Version:** 1.0.0
> **Repo:** https://github.com/YH45TUR/carcosa

---

## 📋 Requisitos Previos

- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose** (opcional, recomendado)
- **Git**
- **Chrome/Chromium** (para pruebas de interfaz)

---

## 🚀 Opcion 1: Docker (recomendado)

### Instalacion

```bash
# 1. Clonar el repositorio
git clone https://github.com/YH45TUR/carcosa.git
cd carcosa

# 2. Crear archivo .env para el backend
# En Windows:
copy backend\.env.example backend\.env
# En Linux/Mac:
# cp backend/.env.example backend/.env

# 3. (Opcional) Generar un JWT_SECRET seguro
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Pega el resultado en backend/.env como JWT_SECRET

# 4. Iniciar todos los servicios
docker-compose up --build

# 5. Acceder desde el navegador:
#    Frontend: http://localhost:5173
#    API:      http://localhost:8000
#    Swagger:  http://localhost:8000/docs
```

### Detener

```bash
docker-compose down
```

---

## 🔧 Opcion 2: Manual (backend + frontend separados)

### Backend

```bash
cd backend

# Crear archivo de entorno
copy .env.example .env

# Crear y activar entorno virtual
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo de spaCy para NER legal
python -m spacy download es_core_news_lg

# Iniciar servidor (con DEBUG activado para desarrollo)
set DEBUG=true
uvicorn app.main:app --reload --port 8000

# La API estara disponible en: http://localhost:8000
# Documentacion Swagger: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# La aplicacion estara disponible en: http://localhost:5173
```

---

## ✅ Checklist de Verificacion

### 1. Backend funcionando

```bash
# Health check simple
curl http://localhost:8000/health
# Respuesta esperada: {"status":"healthy"}

# Root
curl http://localhost:8000/
# Respuesta esperada: {"app":"Sistema Legal CO","status":"online","docs":"/docs"}
```

### 2. Frontend cargando

- Abrir `http://localhost:5173` en el navegador
- Deberias ver la pantalla de login con:
  - Titulo "Sistema Legal CO"
  - Campo de usuario
  - Campo de contraseña
  - Boton "Iniciar sesion"
  - Enlace "Registrate"

### 3. Flujo de autenticacion

```bash
# Registrar un usuario
curl -X POST http://localhost:8000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"test\",\"email\":\"test@test.com\",\"password\":\"Test123!\",\"role\":\"abogado\"}"

# Login
curl -X POST http://localhost:8000/api/auth/login ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=test&password=Test123!"

# Obtener perfil (reemplaza TOKEN con el access_token obtenido)
curl http://localhost:8000/api/auth/me ^
  -H "Authorization: Bearer TOKEN"
```

### 4. Pruebas de modulos

```bash
# Listar casos (requiere token)
curl http://localhost:8000/api/cases/ ^
  -H "Authorization: Bearer TOKEN"

# Listar reglas de auditoria
curl http://localhost:8000/api/audit/reglas ^
  -H "Authorization: Bearer TOKEN"

# Ver fuentes de jurisprudencia
curl http://localhost:8000/api/jurisprudence/sources ^
  -H "Authorization: Bearer TOKEN"

# Ver terminos de la calculadora
curl http://localhost:8000/api/calculator/lista ^
  -H "Authorization: Bearer TOKEN"

# Ver perspectivas adversariales
curl http://localhost:8000/api/adversarial/perspectives ^
  -H "Authorization: Bearer TOKEN"
```

### 5. Rate limiting (verificar que funciona)

```bash
# Hacer mas de 10 intentos de login en 1 minuto
# El intento #11 deberia recibir un HTTP 429 Too Many Requests
for /L %i in (1,1,12) do (
  curl -s -o /dev/null -w "%%{http_code} " ^
    -X POST http://localhost:8000/api/auth/login ^
    -H "Content-Type: application/x-www-form-urlencoded" ^
    -d "username=test&password=wrong"
)
```

---

## 🧪 Tests Automaticos

### Backend (160 tests)

```bash
cd backend

# Ejecutar todos los tests
set TESTING=true
pytest tests/ -v

# Solo tests de un modulo
pytest tests/test_audit.py -v
pytest tests/test_drafting.py -v
pytest tests/test_extraction.py -v
pytest tests/test_fase6.py -v
pytest tests/test_jurisprudence.py -v
pytest tests/test_integration.py -v

# Tests con cobertura
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term
```

### Frontend (typecheck)

```bash
cd frontend

# Verificar TypeScript
npx tsc --noEmit

# Build de produccion
npm run build
```

---

## 🐳 Produccion (Docker)

```bash
# Iniciar con PostgreSQL en lugar de SQLite
docker-compose -f docker-compose.production.yml up --build -d

# Ver logs
docker-compose -f docker-compose.production.yml logs -f
```

---

## 🤖 Probar Chat con IA

Para una experiencia completa del chat legal necesitas **Ollama**:

```bash
# 1. Instalar Ollama: https://ollama.com/download
# 2. Descargar modelo
ollama pull llama3.1:8b

# 3. El backend ya esta configurado para usar Ollama por defecto
#    (LLM_PROVIDER=ollama, OLLAMA_BASE_URL=http://localhost:11434)
```

Si no tienes Ollama, puedes configurar otro proveedor en `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-tu-api-key
```

---

## 🔐 Variables de Entorno (backend/.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./sistema_legal.db` | SQLite (dev) o PostgreSQL (prod) |
| `LLM_PROVIDER` | `ollama` | ollama, openai, gemini, claude, openrouter |
| `JWT_SECRET` | `cambiar_en_produccion...` | **Cambiar en produccion!** |
| `DEBUG` | `false` | `true` para desarrollo (verbose errors) |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | `10` | Max intentos de login por minuto |
| `RATE_LIMIT_CHAT_PER_MINUTE` | `30` | Max mensajes de chat por minuto |

---

## 📊 Estructura de Tests

```
backend/tests/
├── conftest.py           # Configuracion (TESTING=true automatico)
├── test_audit.py         # 33 tests - Auditoria legal con reglas
├── test_drafting.py      # 28 tests - Redaccion juridica DOCX/PDF
├── test_extraction.py    # 23 tests - Extraccion PDF/DOCX/OCR/NER
├── test_fase6.py         # 33 tests - Fase 6 (todo el modulo)
├── test_jurisprudence.py # 22 tests - Busqueda y RAG
└── test_integration.py   # 15 tests - Health/Auth/CORS/Rutas

Total: ~160 tests, 0 fallos esperados
```
