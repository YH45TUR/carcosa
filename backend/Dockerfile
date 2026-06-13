FROM python:3.12-slim

# ─── Dependencias del sistema ─────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR + idioma español (reemplaza PaddleOCR como engine principal)
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-osd \
    # ocrmypdf requiere ghostscript y unpaper
    ghostscript \
    unpaper \
    # LibreOffice headless — exportación PDF con formato NTC 1486
    # Reemplaza WeasyPrint (problemas con fuentes + CSS limitado en Linux)
    libreoffice-writer \
    libreoffice-common \
    libreoffice-java-common \
    default-jre-headless \
    # Fuentes — NTC 1486 requiere Times New Roman
    fonts-liberation \
    fonts-dejavu \
    # Herramientas PDF
    poppler-utils \
    # Misceláneos
    libgl1 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Modelo spaCy español
RUN python -m spacy download es_core_news_lg

COPY . .

# Directorios de datos
RUN mkdir -p data/uploads data/jurisprudence data/chroma

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
