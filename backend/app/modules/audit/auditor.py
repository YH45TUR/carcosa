"""
Sistema Legal CO - Auditor Legal
Motor de auditoría que combina reglas automatizadas + análisis LLM.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.modules.audit.rules import (
    ReglasAuditoria, ResultadoAuditoria, Hallazgo, Criticidad
)


class LegalAuditor:
    """
    Auditor legal colombiano.

    Pipeline:
    1. Ejecuta reglas automatizadas (CGP, CPACA, CPP)
    2. Si hay LLM disponible, hace análisis semántico
    3. Genera reporte estructurado con hallazgos por criticidad
    """

    async def audit_case(
        self,
        case_id: Optional[int],
        message: str,
        document_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Audita un caso o documento legal.

        Args:
            case_id: ID del caso (opcional)
            message: Mensaje del usuario describiendo qué auditar
            document_text: Texto del documento a auditar

        Returns:
            Reporte de auditoría estructurado
        """
        resultado = ResultadoAuditoria()

        # Paso 1: Reglas automatizadas
        if document_text:
            auto_hallazgos = ReglasAuditoria.validate_text(document_text)
            for h in auto_hallazgos:
                resultado.add(h)

        # Paso 2: Análisis LLM (si está disponible)
        llm_hallazgos = await self._analyze_with_llm(message, document_text)
        for h in llm_hallazgos:
            resultado.add(h)

        # Paso 3: Reporte
        resultado.generar_resumen()

        return {
            "success": True,
            "response": resultado.resumen,
            "data": {
                "total_hallazgos": resultado.total_hallazgos,
                "criticos": resultado.criticos,
                "altos": resultado.altos,
                "medios": resultado.medios,
                "bajos": resultado.bajos,
                "hallazgos": [
                    {
                        "criticidad": h.criticidad.value,
                        "categoria": h.categoria.value,
                        "titulo": h.titulo,
                        "descripcion": h.descripcion,
                        "norma": h.norma,
                        "sugerencia": h.sugerencia,
                        "codigo": h.codigo,
                    }
                    for h in resultado.hallazgos
                ],
                "fecha": resultado.fecha,
            },
        }

    async def audit_document(
        self,
        document_text: str,
        codigo: str = "CGP",
    ) -> Dict[str, Any]:
        """
        Audita un documento legal contra un código específico.

        Args:
            document_text: Texto completo del documento
            codigo: Código procesal (CGP, CPACA, CPP)

        Returns:
            Reporte de auditoría
        """
        resultado = ResultadoAuditoria()

        # Reglas específicas del código + generales
        reglas = (
            ReglasAuditoria.get_rules_by_code(codigo) +
            ReglasAuditoria.REGLAS_GENERALES
        )

        for regla in reglas:
            if regla.automatizable:
                resultado.add(regla)

        # Validación automatizada
        auto_hallazgos = ReglasAuditoria.validate_text(document_text)
        for h in auto_hallazgos:
            if h not in resultado.hallazgos:
                resultado.add(h)

        resultado.generar_resumen()

        return {
            "success": True,
            "response": resultado.resumen,
            "data": {
                "codigo": codigo,
                "total_hallazgos": resultado.total_hallazgos,
                "criticos": resultado.criticos,
                "altos": resultado.altos,
                "medios": resultado.medios,
                "bajos": resultado.bajos,
                "hallazgos": [
                    {
                        "criticidad": h.criticidad.value,
                        "categoria": h.categoria.value,
                        "titulo": h.titulo,
                        "descripcion": h.descripcion,
                        "codigo": h.codigo,
                    }
                    for h in resultado.hallazgos
                ],
            },
        }

    async def _analyze_with_llm(
        self,
        message: str,
        document_text: Optional[str] = None,
    ) -> List[Hallazgo]:
        """
        Análisis semántico usando LLM para detectar hallazgos no automatizables.

        Si no hay LLM disponible, retorna lista vacía.
        """
        hallazgos = []

        try:
            from app.core.llm import LLMClient

            llm = LLMClient()
            system_prompt = (
                "Eres un auditor legal experto en derecho procesal colombiano. "
                "Analiza el texto y detecta hallazgos con esta estructura JSON:\n"
                "{\n"
                '  "hallazgos": [{\n'
                '    "criticidad": "crítico|alto|medio|bajo",\n'
                '    "titulo": "...",\n'
                '    "descripcion": "...",\n'
                '    "norma": "Artículo X del Código...",\n'
                '    "sugerencia": "..."\n'
                "  }]\n"
                "}\n\n"
                "Solo incluye hallazgos verdaderos, no inventes."
            )

            prompt = message
            if document_text:
                prompt += f"\n\nDocumento a auditar:\n{document_text[:10000]}"

            response = await llm.chat(
                message=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
            )

            # Intentar parsear JSON del LLM
            import json
            import re

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for h in data.get("hallazgos", []):
                    try:
                        criticidad = Criticidad(h.get("criticidad", "bajo"))
                    except ValueError:
                        criticidad = Criticidad.BAJO

                    from app.modules.audit.rules import Categoria
                    cat_guess = Categoria.FORMA
                    hallazgos.append(Hallazgo(
                        criticidad=criticidad,
                        categoria=cat_guess,
                        titulo=h.get("titulo", "Hallazgo sin título"),
                        descripcion=h.get("descripcion", ""),
                        norma=h.get("norma", ""),
                        sugerencia=h.get("sugerencia", ""),
                        automatizable=False,
                    ))

        except Exception:
            # Sin LLM, solo reglas automatizadas
            pass

        return hallazgos
