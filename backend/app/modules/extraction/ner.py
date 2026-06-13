"""
Sistema Legal CO - NER Legal
Extracción de entidades legales colombianas usando spaCy + regex.

Entidades extraídas:
- RADICADO: Número de radicado (Ej: 11001-31-03-001-2024-00001-00)
- JUZGADO: Juzgado/Despacho (Ej: Juzgado 1° Civil del Circuito de Bogotá)
- PARTES: Actor, demandado, terceros
- FECHAS: Fechas clave del proceso
- NORMAS: Leyes, decretos, artículos citados
- CUANTIA: Valor del proceso
- TIPO_PROCESO: Tipo de proceso legal
"""
from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime


class LegalNER:
    """
    Extractor de entidades legales colombianas.

    Usa spaCy como base con reglas específicas para el dominio legal colombiano.
    """

    # Patrones de radicados colombianos
    RADICADO_PATTERNS = [
        r'\d{5}-\d{2}-\d{3}-\d{3}-\d{4}-\d{5}-\d{2}',  # Formato completo
        r'\d{5}-\d{2}-\d{3}-\d{3}-\d{4}-\d{5}',          # Sin dígito de verificación
        r'\d{5}-\d{2}-\d{3}-\d{3}-\d{4}',                 # Formato corto
        r'\d{4}-\d{2}-\d{2}-\d{4}',                       # Formato alternativo
        r'Radicado\s*[:\-]?\s*[\d\-]+\d',                 # Con palabra radicado
    ]

    # Patrones de juzgados/despachos
    JUZGADO_PATTERNS = [
        # Juzgado con número ordinal escrito en letras o dígitos
        r'(?:Juzgado|JUZGADO)\s+(?:\d+[°º]?|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|DÉCIMO|Primero|Segundo|Tercero|Cuarto|Quinto|Sexto|Séptimo|Octavo|Noveno|Décimo)\s+(?:Civil|Penal|Laboral|Familia|Promiscuo|Administrativo|Ejecución|Garantías|Conocimiento)',
        r'(?:Tribunal|Corte|Consejo)\s+(?:Superior|Supremo|de\s+Estado|Constitucional|Seccional)',
        r'(?:Sala\s+(?:Civil|Penal|Laboral|Plena|Administrativa|Casación))\s+(?:del|de\s+la)?\s*(?:Tribunal|Corte)?',
        r'Juzgado\s+(?:\d+[°º]?|Primer[ao]|Segund[ao]|Tercer[ao])\s+\w+\s+(?:del\s+Circuito|Municipal|Promiscuo)',
        r'Despacho\s+Judicial\s+[\w\s]+',
        r'Fiscalía\s+\d+[°º]?\s+(?:Local|Seccional|Delegada)',
        # Juzgado con formato completo: JUZGADO PRIMERO CIVIL DEL CIRCUITO DE CIUDAD
        r'JUZGADO\s+\w+\s+(?:CIVIL|PENAL|LABORAL|FAMILIA|PROMISCUO|ADMINISTRATIVO)\s+DEL\s+\w+\s+(?:DE\s+)?\w+',
        # Juzgado con ordinal: Juzgado 1° Civil del Circuito de Ciudad
        r'Juzgado\s+\d+[°º]?\s+\w+\s+del\s+Circuito\s+de\s+\w+',
    ]

    # Patrones de normas legales colombianas
    NORMA_PATTERNS = [
        r'(?:Ley|L\.)\s+\d+\s+de\s+\d{4}',
        r'(?:Decreto|D\.)\s+\d+\s+de\s+\d{4}',
        r'(?:Sentencia|S\.)\s+(?:T|C|SU|A)\s+\d+[-\s]\d{4}',
        r'(?:Artículo|Art\.?)\s+\d+',
        r'(?:Código|C\.)\s+(?:Civil|Penal|Laboral|Comercio|General\s+del\s+Proceso|Contencioso\s+Administrativo)',
        r'(?:C\.G\.P\.|C\.P\.A\.C\.A\.|C\.P\.P\.|C\.S\.T\.)',
        r'(?:Resolución|R\.)\s+\d+\s+de\s+\d{4}',
        r'(?:Acuerdo|Circular|Directiva)\s+\d+\s+de\s+\d{4}',
        r'Constitución\s+Política\s+de\s+Colombia',
        r'C\.P\.(?:C\.)?',
        r'Ley\s+\d+[\.\d]*\s*\(?\d{4}\)?',
    ]

    # Patrones de cuantías
    CUANTIA_PATTERNS = [
        r'(?:\$|COP|pesos)\s*[\d.,]+\s*(?:millones|mil|billones)?',
        r'(?:cuantía|Cuantía|valor|Valor)\s*(?:de|:)?\s*\$?\s*[\d.,]+',
        r'[\d.,]+\s*(?:UVT|salarios\s+mínimos)',
        r'\$\s*[\d.,]+\s*(?:millones|mil|billones)?\s*(?:de\s*pesos)?',
    ]

    # Patrones de fechas
    FECHA_PATTERNS = [
        r'\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}\s+de\s+(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\.?\s+de\s+\d{4}',
    ]

    # Palabras clave para tipos de proceso
    TIPO_PROCESO_KEYWORDS = {
        "VERBAL": ["verbal", "proceso verbal", "declarativo"],
        "TUTELA": ["tutela", "acción de tutela", "amparo constitucional"],
        "EJECUTIVO": ["ejecutivo", "ejecutivo singular", "ejecutivo hipotecario"],
        "ORDINARIO": ["ordinario", "proceso ordinario"],
        "LABORAL": ["ordinaria laboral", "ordinario laboral", "proceso laboral", "laboral"],
        "FAMILIA": ["divorcio", "custodia", "alimentos", "filiación", "sucesión"],
        "PENAL": ["penal", "investigación", "causa penal"],
        "CONTENCIOSO": ["nulidad", "reparación directa", "contractual", "contencioso"],
        "CONSTITUCIONAL": ["inconstitucionalidad", "constitucional"],
        "ARBITRAL": ["arbitraje", "arbitral", "laudo"],
    }

    def __init__(self):
        self._nlp = None
        self._spacy_available = False

        try:
            import spacy
            self._spacy = spacy

            try:
                self._nlp = spacy.load("es_core_news_lg")
                self._spacy_available = True
            except OSError:
                try:
                    self._nlp = spacy.load("es_core_news_md")
                    self._spacy_available = True
                except OSError:
                    try:
                        self._nlp = spacy.load("es_core_news_sm")
                        self._spacy_available = True
                    except OSError:
                        self._spacy_available = False
        except ImportError:
            self._spacy_available = False

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extrae todas las entidades legales del texto.

        Args:
            text: Texto del documento legal

        Returns:
            Diccionario con todas las entidades encontradas
        """
        if not text or not text.strip():
            return self._empty_result()

        entities = {
            "radicados": self._extract_radicados(text),
            "juzgados": self._extract_juzgados(text),
            "normas": self._extract_normas(text),
            "fechas": self._extract_fechas(text),
            "cuantias": self._extract_cuantias(text),
            "tipo_proceso": self._extract_tipo_proceso(text),
            "partes": self._extract_partes(text),
        }

        # Enriquecer con spaCy si está disponible
        if self._spacy_available:
            spacy_entities = await self._extract_with_spacy(text)
            entities["personas"] = spacy_entities.get("personas", [])
            entities["organizaciones"] = spacy_entities.get("organizaciones", [])
            entities["ubicaciones"] = spacy_entities.get("ubicaciones", [])
        else:
            entities["personas"] = []
            entities["organizaciones"] = []
            entities["ubicaciones"] = []

        # Resumen de entidades encontradas
        entities["total_entities"] = sum(len(v) for v in entities.values() if isinstance(v, list))

        return entities

    def _extract_radicados(self, text: str) -> List[Dict[str, Any]]:
        """Extrae números de radicado."""
        results = []
        for pattern in self.RADICADO_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                raw = match.group().strip()
                # Extraer solo los dígitos y guiones del radicado
                nums = re.search(r'[\d][\d\-]+', raw)
                radicado = nums.group() if nums else raw
                if radicado and radicado not in [r["value"] for r in results]:
                    results.append({
                        "value": radicado,
                        "type": "RADICADO",
                        "confidence": 0.9,
                    })
        return results

    def _extract_juzgados(self, text: str) -> List[Dict[str, Any]]:
        """Extrae nombres de juzgados/despachos."""
        results = []
        for pattern in self.JUZGADO_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                juzgado = match.group().strip()
                if juzgado and juzgado not in [r["value"] for r in results]:
                    results.append({
                        "value": juzgado,
                        "type": "JUZGADO",
                        "confidence": 0.85,
                    })
        return results

    def _extract_normas(self, text: str) -> List[Dict[str, Any]]:
        """Extrae normas legales citadas."""
        results = []
        for pattern in self.NORMA_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                norma = match.group().strip()
                if norma and norma not in [r["value"] for r in results]:
                    results.append({
                        "value": norma,
                        "type": "NORMA",
                        "confidence": 0.8,
                    })
        return results

    def _extract_fechas(self, text: str) -> List[Dict[str, Any]]:
        """Extrae fechas del texto."""
        results = []
        for pattern in self.FECHA_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fecha = match.group().strip()
                if fecha and fecha not in [r["value"] for r in results]:
                    results.append({
                        "value": fecha,
                        "type": "FECHA",
                        "confidence": 0.9,
                    })
        return results

    def _extract_cuantias(self, text: str) -> List[Dict[str, Any]]:
        """Extrae cuantías del proceso."""
        results = []
        for pattern in self.CUANTIA_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                cuantia = match.group().strip()
                if cuantia and cuantia not in [r["value"] for r in results]:
                    results.append({
                        "value": cuantia,
                        "type": "CUANTIA",
                        "confidence": 0.75,
                    })
        return results

    def _extract_tipo_proceso(self, text: str) -> List[Dict[str, Any]]:
        """Determina el tipo de proceso legal."""
        text_lower = text.lower()
        found_types = []

        for tipo, keywords in self.TIPO_PROCESO_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_types.append({
                        "value": tipo,
                        "keyword": keyword,
                        "type": "TIPO_PROCESO",
                        "confidence": 0.7,
                    })
                    break

        return found_types

    def _extract_partes(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae las partes del proceso (actor, demandado).
        Usa patrones de encabezados comunes en documentos colombianos.
        """
        partes = {
            "actor": [],
            "demandado": [],
            "terceros": [],
        }

        # Buscar secciones de partes
        lines = text.split("\n")
        current_section = None

        for line in lines:
            line_lower = line.strip().lower()

            if any(p in line_lower for p in ["actor:", "demandante:", "accionante:", "solicitante:"]):
                current_section = "actor"
                value = self._clean_parte(line)
                if value:
                    partes["actor"].append(value)
            elif any(p in line_lower for p in ["demandado:", "accionado:", "opositor:"]):
                current_section = "demandado"
                value = self._clean_parte(line)
                if value:
                    partes["demandado"].append(value)
            elif "tercero" in line_lower:
                current_section = "terceros"
                value = self._clean_parte(line)
                if value:
                    partes["terceros"].append(value)
            elif current_section and line.strip() and ":" not in line:
                partes[current_section].append(line.strip())

        return partes

    def _clean_parte(self, line: str) -> Optional[str]:
        """Limpia el nombre de una parte del proceso."""
        # Remover el label
        for prefix in ["Actor:", "Demandante:", "Demandado:", "Accionante:", 
                       "Accionado:", "Solicitante:", "Opositor:", "Tercero:"]:
            if prefix.lower() in line.lower():
                line = line.split(":", 1)[1].strip() if ":" in line else line

        # Limpiar
        line = line.strip().strip(".,;:")
        return line if line and len(line) > 3 else None

    async def _extract_with_spacy(self, text: str) -> Dict[str, List[str]]:
        """Extrae entidades usando spaCy."""
        if not self._nlp:
            return {"personas": [], "organizaciones": [], "ubicaciones": []}

        doc = self._nlp(text[:50000])  # Limitar tamaño para rendimiento

        entities = {
            "personas": [],
            "organizaciones": [],
            "ubicaciones": [],
        }

        for ent in doc.ents:
            label = ent.label_
            text_val = ent.text.strip()

            if not text_val or len(text_val) < 3:
                continue

            if label == "PER":
                if text_val not in entities["personas"]:
                    entities["personas"].append(text_val)
            elif label in ("ORG", "MISC"):
                if text_val not in entities["organizaciones"]:
                    entities["organizaciones"].append(text_val)
            elif label == "LOC":
                if text_val not in entities["ubicaciones"]:
                    entities["ubicaciones"].append(text_val)

        return entities

    def _empty_result(self) -> Dict[str, Any]:
        """Resultado vacío para textos sin contenido."""
        return {
            "radicados": [],
            "juzgados": [],
            "normas": [],
            "fechas": [],
            "cuantias": [],
            "tipo_proceso": [],
            "partes": {"actor": [], "demandado": [], "terceros": []},
            "personas": [],
            "organizaciones": [],
            "ubicaciones": [],
            "total_entities": 0,
        }
