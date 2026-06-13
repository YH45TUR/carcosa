"""
Sistema Legal CO - Analizador de Testimonios
Extracción de declaraciones, detección de contradicciones y resumen ejecutivo.
"""
from typing import Optional, Dict, Any, List
import re


class TestimonyAnalyzer:
    """
    Analiza testimonios y declaraciones en documentos legales.

    Capacidades:
    - Extracción de declaraciones textuales
    - Detección de contradicciones internas
    - Identificación de hechos clave, personas y fechas
    - Generación de resumen ejecutivo
    """

    # Patrones para detectar declaraciones
    DECLARATION_PATTERNS = [
        r'(?:Manifestó|Declaró|Afirmó|Sostuvo|Expresó|Indicó|Señaló|Dijo|Aseguró|Expuso|Narró|Contestó|Respondió)\s+que\s+([^\.]+)',
        r'(?:Bajo\s+juramento|Bajo\s+la\s+gravedad)\s+[^\.]+',
        r'DECLARACIÓN[^:]*:\s*([^\.]+)',
        r'"[^"]{20,}"',  # Citas textuales largas
    ]

    # Palabras de contradicción
    CONTRADICTION_MARKERS = [
        "pero", "sin embargo", "no obstante", "contrario a",
        "contradice", "contradictorio", "inconsistente",
        "por un lado", "por otro lado",
        "antes dijo", "después dijo",
        "versus", "vs",
    ]

    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analiza un texto en busca de testimonios y declaraciones.

        Args:
            text: Texto del documento legal

        Returns:
            Análisis completo con declaraciones, contradicciones y resumen
        """
        if not text or not text.strip():
            return self._empty_result()

        # Extraer declaraciones
        declaraciones = self._extract_declarations(text)

        # Detectar contradicciones
        contradicciones = self._detect_contradictions(declaraciones, text)

        # Identificar personas mencionadas
        personas = self._extract_persons(text)

        # Identificar hechos clave
        hechos_clave = self._extract_key_facts(text)

        # Resumen ejecutivo
        resumen = self._generate_summary(declaraciones, contradicciones, hechos_clave)

        return {
            "declaraciones": declaraciones,
            "contradicciones": contradicciones,
            "personas_mencionadas": personas,
            "hechos_clave": hechos_clave,
            "resumen": resumen,
            "total_declaraciones": len(declaraciones),
            "total_contradicciones": len(contradicciones),
        }

    def _extract_declarations(self, text: str) -> List[Dict[str, Any]]:
        """Extrae declaraciones del texto usando patrones."""
        declaraciones = []

        for pattern in self.DECLARATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Tomar el grupo capturado o el match completo
                declaracion = (match.group(1) if match.lastindex else match.group(0)).strip()

                if declaracion and len(declaracion) > 15:
                    # Determinar quién declaró
                    context_start = max(0, match.start() - 200)
                    context = text[context_start:match.start()]

                    declarante = self._identify_speaker(context, match.group(0))

                    # Tipo de declaración
                    tipo = self._classify_declaration(match.group(0))

                    declaraciones.append({
                        "texto": declaracion[:500],
                        "declarante": declarante,
                        "tipo": tipo,
                        "contexto": context[-150:] if context else "",
                    })

        return declaraciones

    def _identify_speaker(self, context: str, match: str) -> str:
        """Identifica quién hizo la declaración basado en el contexto."""
        # Buscar nombres antes de la declaración
        name_patterns = [
            r'(?:el\s+)?(?:Sr\.?|Señor|Sra\.?|Señora|Dr\.?|Doctor|Dra\.?|Doctora)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
            r'(?:el\s+)?(?:testigo|perito|demandante|demandado|accionante|accionado)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
        ]

        for pattern in name_patterns:
            name_match = re.search(pattern, context[-200:], re.IGNORECASE)
            if name_match:
                return name_match.group(1).strip()

        # Fallback: tipo de persona jurídica
        if "testigo" in context.lower():
            return "Testigo"
        elif "perito" in context.lower():
            return "Perito"
        elif "demandante" in context.lower() or "accionante" in context.lower():
            return "Demandante"
        elif "demandado" in context.lower() or "accionado" in context.lower():
            return "Demandado"

        return "Declarante no identificado"

    def _classify_declaration(self, text: str) -> str:
        """Clasifica el tipo de declaración."""
        text_lower = text.lower()

        if any(w in text_lower for w in ["juramento", "juro", "bajo la gravedad"]):
            return "bajo_juramento"
        elif any(w in text_lower for w in ["preguntado", "interrogado", "repreguntado"]):
            return "interrogatorio"
        elif any(w in text_lower for w in ["manifiesto", "declaro", "expongo"]):
            return "declaracion_voluntaria"
        elif any(w in text_lower for w in ["afirmó", "aseguró", "sostuvo"]):
            return "afirmacion"
        else:
            return "declaracion_libre"

    def _detect_contradictions(
        self,
        declaraciones: List[Dict[str, Any]],
        text: str,
    ) -> List[Dict[str, Any]]:
        """
        Detecta contradicciones internas entre declaraciones.
        Busca declaraciones del mismo declarante que se contradigan.
        """
        contradicciones = []

        # Buscar marcadores de contradicción en el texto
        for marker in self.CONTRADICTION_MARKERS:
            pattern = f'([^.]*{marker}[^.]*\\.)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                contradicciones.append({
                    "tipo": "marcador_textual",
                    "marcador": marker,
                    "texto": match.group(1).strip()[:300],
                    "severidad": "media",
                })

        # Buscar contradicciones entre declaraciones del mismo declarante
        por_declarante = {}
        for d in declaraciones:
            nombre = d["declarante"]
            if nombre not in por_declarante:
                por_declarante[nombre] = []
            por_declarante[nombre].append(d["texto"])

        for declarante, textos in por_declarante.items():
            if len(textos) >= 2:
                # Comparar pares de declaraciones
                for i in range(len(textos)):
                    for j in range(i + 1, len(textos)):
                        similitud = self._text_similarity(textos[i], textos[j])
                        if similitud > 0.7:
                            contradicciones.append({
                                "tipo": "contradiccion_interna",
                                "declarante": declarante,
                                "declaracion_1": textos[i][:200],
                                "declaracion_2": textos[j][:200],
                                "similitud": round(similitud, 2),
                                "severidad": "alta",
                            })

        return contradicciones

    def _extract_persons(self, text: str) -> List[str]:
        """Extrae nombres de personas mencionadas en el texto."""
        persons = set()
        # Patrón básico de nombre completo en español
        patterns = [
            r'(?:el\s+)?(?:Sr\.?|Señor|Sra\.?|Señora|Dr\.?|Doctor|Dra\.?|Doctora)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                persons.add(match.strip())

        return sorted(persons)

    def _extract_key_facts(self, text: str) -> List[Dict[str, str]]:
        """Extrae hechos clave del texto."""
        hechos = []

        # Buscar fechas con eventos
        date_pattern = r'(\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4})'
        matches = re.finditer(date_pattern, text, re.IGNORECASE)
        for match in matches:
            fecha = match.group(1)
            # Tomar el contexto alrededor de la fecha
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            contexto = text[start:end].strip()
            hechos.append({
                "fecha": fecha,
                "contexto": re.sub(r'\s+', ' ', contexto)[:200],
            })

        return hechos

    def _generate_summary(
        self,
        declaraciones: List[Dict[str, Any]],
        contradicciones: List[Dict[str, Any]],
        hechos_clave: List[Dict[str, str]],
    ) -> str:
        """Genera un resumen ejecutivo del análisis de testimonios."""
        lines = [
            "📋 ANÁLISIS DE TESTIMONIOS - RESUMEN EJECUTIVO",
            f"",
            f"Declaraciones encontradas: {len(declaraciones)}",
            f"Contradicciones detectadas: {len(contradicciones)}",
            f"Hechos clave identificados: {len(hechos_clave)}",
            f"",
        ]

        if declaraciones:
            lines.append("DECLARACIONES:")
            for d in declaraciones[:5]:  # Top 5
                lines.append(f"  • [{d['tipo']}] {d['declarante']}: {d['texto'][:100]}...")
            if len(declaraciones) > 5:
                lines.append(f"  ... y {len(declaraciones) - 5} más")

        if contradicciones:
            lines.append(f"\nCONTRADICCIONES:")
            for c in contradicciones[:3]:
                if c["tipo"] == "marcador_textual":
                    lines.append(f"  ⚠️ [{c['severidad']}] {c['texto'][:150]}...")
                else:
                    lines.append(f"  ⚠️ [{c['severidad']}] {c['declarante']} "
                                 f"se contradice (similitud: {c.get('similitud', 'N/A')})")

        if hechos_clave:
            lines.append(f"\nHECHOS CLAVE:")
            for h in hechos_clave[:5]:
                lines.append(f"  📅 {h['fecha']}: {h['contexto'][:100]}...")

        return "\n".join(lines)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud simple entre dos textos (0-1)."""
        words1 = set(text1.lower().split()[:20])
        words2 = set(text2.lower().split()[:20])

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _empty_result(self) -> Dict[str, Any]:
        """Resultado vacío para textos sin contenido."""
        return {
            "declaraciones": [],
            "contradicciones": [],
            "personas_mencionadas": [],
            "hechos_clave": [],
            "resumen": "No hay texto para analizar.",
            "total_declaraciones": 0,
            "total_contradicciones": 0,
        }
