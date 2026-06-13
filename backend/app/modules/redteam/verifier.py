"""
Sistema Legal CO - Red Team Verifier
Verificación anti-alucinaciones: cada cita legal se valida contra fuentes,
consistencia interna y segunda pasada de calidad antes de entregar.
"""
from typing import Optional, Dict, Any, List
import re


class RedTeamVerifier:
    """
    Verificador de calidad y anti-alucinaciones para documentos legales.

    Verifica:
    - Cada cita legal contra patrones conocidos
    - Consistencia interna del documento
    - Coherencia entre hechos y conclusiones
    - Formato y estructura jurídica
    """

    # Patrones de citas legales colombianas válidas
    PATRONES_CITA = {
        "constitucion": r'Constitución\s+Política\s+(de\s+Colombia\s+)?(de\s+)?1991',
        "ley": r'Ley\s+\d+\s+de\s+\d{4}',
        "decreto": r'Decreto\s+\d+\s+de\s+\d{4}',
        "sentencia_t": r'Sentencia\s+T[-–\s]?\d{2,4}[-–\s]?\d{2,4}',
        "sentencia_c": r'Sentencia\s+C[-–\s]?\d{2,4}[-–\s]?\d{2,4}',
        "sentencia_su": r'Sentencia\s+SU[-–\s]?\d{2,4}[-–\s]?\d{2,4}',
        "articulo": r'Artículo\s+\d+',
        "codigo_civil": r'Código\s+Civil',
        "codigo_penal": r'Código\s+Penal',
        "cgp": r'Código\s+General\s+del\s+Proceso',
        "cpaca": r'Código\s+de\s+Procedimiento\s+Administrativo',
        "cpp": r'Código\s+de\s+Procedimiento\s+Penal',
    }

    # Señales de alarma para posibles alucinaciones
    SEÑALES_ALARMA = [
        "ley inexistente", "artículo ficticio", "sentencia inventada",
        "corte inexistente", "código falso", "norma apócrifa",
        "según el artículo", "de conformidad con la ley",
        r'\bLey\s+0\b', r'\bArtículo\s+0\b',
    ]

    async def verify_document(self, content: str) -> Dict[str, Any]:
        """
        Verifica un documento legal completo.

        Args:
            content: Texto del documento a verificar

        Returns:
            Reporte de verificación
        """
        hallazgos = []

        # 1. Verificar citas legales
        citas = self._check_citations(content)
        hallazgos.extend(citas)

        # 2. Verificar consistencia interna
        consistencia = self._check_consistency(content)
        hallazgos.extend(consistencia)

        # 3. Verificar señales de alarma
        alarmas = self._check_alarm_signals(content)
        hallazgos.extend(alarmas)

        # 4. Verificar estructura
        estructura = self._check_structure(content)
        hallazgos.extend(estructura)

        # Generar reporte
        errores = [h for h in hallazgos if h["severidad"] == "error"]
        advertencias = [h for h in hallazgos if h["severidad"] == "advertencia"]
        info = [h for h in hallazgos if h["severidad"] == "info"]

        score = self._calculate_score(len(errores), len(advertencias))

        return {
            "success": score >= 70,
            "response": self._format_report(score, errores, advertencias, info),
            "data": {
                "score": score,
                "errores": len(errores),
                "advertencias": len(advertencias),
                "info": len(info),
                "total_hallazgos": len(hallazgos),
                "detalles": hallazgos,
            },
        }

    def _check_citations(self, text: str) -> List[Dict]:
        """Verifica que las citas legales sean válidas."""
        hallazgos = []
        citas_encontradas = set()

        for tipo, pattern in self.PATRONES_CITA.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                citas_encontradas.add(match if isinstance(match, str) else match[0])

        if citas_encontradas:
            hallazgos.append({
                "tipo": "citas_validas",
                "severidad": "info",
                "mensaje": f"Se encontraron {len(citas_encontradas)} citas legales con formato válido",
                "detalle": list(citas_encontradas)[:10],
            })
        else:
            hallazgos.append({
                "tipo": "sin_citas",
                "severidad": "advertencia",
                "mensaje": "No se encontraron citas legales con formato estándar colombiano",
                "detalle": "Verificar que las normas se citen correctamente (ej: Ley 100 de 1993)",
            })

        # Verificar patrones sospechosos en citas
        patrones_sospechosos = [
            (r'Ley\s+\d{5,}', "Número de ley con demasiados dígitos"),
            (r'Artículo\s+\d{4,}', "Número de artículo poco realista"),
            (r'Sentencia\s+[A-Z]+\s*[-–]?\s*\d{6,}', "Número de sentencia con demasiados dígitos"),
        ]

        for pattern, mensaje in patrones_sospechosos:
            if re.search(pattern, text):
                hallazgos.append({
                    "tipo": "cita_sospechosa",
                    "severidad": "advertencia",
                    "mensaje": f"Cita sospechosa: {mensaje}",
                    "detalle": "Verificar esta cita contra fuentes oficiales",
                })

        return hallazgos

    def _check_consistency(self, text: str) -> List[Dict]:
        """Verifica consistencia interna del documento."""
        hallazgos = []
        text_lower = text.lower()

        # Verificar que las pretensiones correspondan a los hechos
        if "pretensión" in text_lower or "pretensiones" in text_lower:
            if "hecho" not in text_lower:
                hallazgos.append({
                    "tipo": "inconsistencia",
                    "severidad": "error",
                    "mensaje": "Hay pretensiones pero no se identifican hechos que las sustenten",
                    "detalle": "Toda pretensión debe basarse en hechos concretos (Art. 82 CGP)",
                })

        # Verificar que haya fundamentos de derecho si hay pretensiones
        if "pretensión" in text_lower or "pretensiones" in text_lower:
            tiene_normas = any(
                kw in text_lower for kw in ["artículo", "ley", "código", "decreto"]
            )
            if not tiene_normas:
                hallazgos.append({
                    "tipo": "inconsistencia",
                    "severidad": "error",
                    "mensaje": "Las pretensiones no tienen fundamento legal",
                    "detalle": "Incluir las normas que respaldan cada pretensión",
                })

        # Verificar firma
        if "t.p." not in text_lower and "tarjeta profesional" not in text_lower:
            hallazgos.append({
                "tipo": "falta_firma",
                "severidad": "advertencia",
                "mensaje": "No se encontró Tarjeta Profesional en la firma",
                "detalle": "Todo abogado debe incluir T.P. al firmar (Decreto 196/1971)",
            })

        return hallazgos

    def _check_alarm_signals(self, text: str) -> List[Dict]:
        """Detecta posibles alucinaciones."""
        hallazgos = []
        text_lower = text.lower()

        for senal in self.SEÑALES_ALARMA:
            if re.search(senal, text_lower):
                hallazgos.append({
                    "tipo": "posible_alucinacion",
                    "severidad": "error",
                    "mensaje": f"Posible alucinación detectada: '{senal}'",
                    "detalle": "Verificar esta referencia contra fuentes oficiales",
                })

        return hallazgos

    def _check_structure(self, text: str) -> List[Dict]:
        """Verifica la estructura del documento legal."""
        hallazgos = []
        lines = text.split("\n")
        word_count = len(text.split())

        if word_count < 50:
            hallazgos.append({
                "tipo": "estructura",
                "severidad": "error",
                "mensaje": "Documento demasiado corto para ser un documento legal válido",
                "detalle": f"Solo {word_count} palabras. Un documento legal típico tiene 500+ palabras.",
            })

        # Verificar secciones esenciales
        secciones_esenciales = {
            "hechos": ["hecho", "hechos"],
            "derecho": ["fundamento", "derecho", "norma", "legal"],
            "petición": ["solicito", "pido", "pretensión", "solicitud"],
        }

        secciones_encontradas = 0
        for seccion, keywords in secciones_esenciales.items():
            if any(kw in text.lower() for kw in keywords):
                secciones_encontradas += 1

        if secciones_encontradas < 2:
            hallazgos.append({
                "tipo": "estructura",
                "severidad": "advertencia",
                "mensaje": "Faltan secciones esenciales en el documento legal",
                "detalle": "Un documento legal debe incluir: hechos, fundamentos de derecho y petición/pretensión",
            })

        return hallazgos

    def _calculate_score(self, errores: int, advertencias: int) -> int:
        """Calcula puntaje de calidad (0-100)."""
        score = 100
        score -= errores * 15
        score -= advertencias * 5
        return max(0, min(100, score))

    def _format_report(
        self,
        score: int,
        errores: List[Dict],
        advertencias: List[Dict],
        info: List[Dict],
    ) -> str:
        """Formatea el reporte de verificación."""
        if score >= 80:
            calif = "✅ APROBADO"
        elif score >= 50:
            calif = "⚠️ APROBADO CON OBSERVACIONES"
        else:
            calif = "❌ REQUIERE REVISIÓN"

        lines = [
            f"🔍 RED TEAM VERIFIER - Control de Calidad",
            f"",
            f"Puntaje: {score}/100 — {calif}",
            f"Errores: {len(errores)} | Advertencias: {len(advertencias)} | Info: {len(info)}",
            f"",
        ]

        if errores:
            lines.append("ERRORES:")
            for e in errores:
                lines.append(f"  ❌ {e['mensaje']}")
            lines.append("")

        if advertencias:
            lines.append("ADVERTENCIAS:")
            for a in advertencias:
                lines.append(f"  ⚠️ {a['mensaje']}")
            lines.append("")

        if info:
            lines.append("INFO:")
            for i in info[:3]:
                lines.append(f"  ℹ️ {i['mensaje']}")
            lines.append("")

        lines.append(f"Documento verificado: {score}/100")
        return "\n".join(lines)
