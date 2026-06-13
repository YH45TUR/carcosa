"""
Sistema Legal CO - Analizador Adversarial
Pipeline unificado para análisis desde perspectivas de juez y contra-parte.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import json
import re

from app.modules.adversarial.prompts import (
    get_perspective, get_available_perspectives
)


class AdversarialAnalyzer:
    """
    Analizador adversarial con dos perspectivas configurables:
    - judge: Ojo del Juez - evaluación imparcial
    - opponent: Contra-Parte Virtual - búsqueda de vulnerabilidades
    """

    async def analyze(
        self,
        document_text: str,
        perspective: str = "judge",
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analiza un documento legal desde una perspectiva específica.

        Args:
            document_text: Texto del documento a analizar
            perspective: 'judge' o 'opponent'
            case_data: Datos del caso (opcional)

        Returns:
            Análisis completo según la perspectiva
        """
        if not document_text or not document_text.strip():
            return {
                "success": False,
                "response": "No hay texto para analizar. Proporciona un documento legal.",
            }

        try:
            config = get_perspective(perspective)
        except ValueError as e:
            return {
                "success": False,
                "response": str(e),
                "available_perspectives": get_available_perspectives(),
            }

        # Análisis con LLM
        analysis = await self._analyze_with_llm(
            document_text=document_text,
            perspective=perspective,
            system_prompt=config["system_prompt"],
            case_data=case_data,
        )

        # Si falló el LLM, usar análisis offline
        if not analysis:
            analysis = self._analyze_offline(document_text, perspective)

        return {
            "success": True,
            "response": self._format_response(analysis, config["name"]),
            "data": {
                "perspective": perspective,
                "perspective_name": config["name"],
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
            },
        }

    async def analyze_both(
        self,
        document_text: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analiza desde ambas perspectivas (juez + contra-parte).
        """
        judge_result = await self.analyze(document_text, "judge", case_data)
        opponent_result = await self.analyze(document_text, "opponent", case_data)

        return {
            "success": True,
            "response": (
                f"⚔️ ANÁLISIS ADVERSARIAL COMPLETO\n\n"
                f"=== PERSPECTIVA DEL JUEZ ===\n"
                f"{judge_result.get('response', '')}\n\n"
                f"=== PERSPECTIVA DE LA CONTRA-PARTE ===\n"
                f"{opponent_result.get('response', '')}"
            ),
            "data": {
                "judge": judge_result.get("data"),
                "opponent": opponent_result.get("data"),
                "timestamp": datetime.now().isoformat(),
            },
        }

    async def _analyze_with_llm(
        self,
        document_text: str,
        perspective: str,
        system_prompt: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Analiza usando LLM con el system prompt de la perspectiva.
        """
        try:
            from app.core.llm import LLMClient

            llm = LLMClient()
            prompt = (
                f"Analiza el siguiente documento legal desde la perspectiva "
                f"de '{perspective}':\n\n"
                f"{document_text[:15000]}"
            )

            if case_data:
                prompt += f"\n\nDatos del caso: {json.dumps(case_data, ensure_ascii=False)}"

            response = await llm.chat(
                message=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            return {
                "analisis_completo": response,
                "tipo_analisis": perspective,
            }

        except Exception:
            return None

    def _analyze_offline(
        self,
        document_text: str,
        perspective: str,
    ) -> Dict[str, Any]:
        """
        Análisis offline cuando el LLM no está disponible.
        Realiza análisis básico basado en reglas.
        """
        text_lower = document_text.lower()
        word_count = len(document_text.split())

        # Indicadores básicos
        tiene_normas = any(
            kw in text_lower
            for kw in ["artículo", "ley", "decreto", "código", "sentencia"]
        )
        tiene_fechas = bool(
            re.search(r'\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', text_lower)
        )
        tiene_pretensiones = "pretensión" in text_lower or "pretensiones" in text_lower
        tiene_pruebas = "prueba" in text_lower or "pruebas" in text_lower
        tiene_fundamentos = "fundamento" in text_lower

        if perspective == "judge":
            return {
                "puntos_confusion": [],
                "fortalezas": [
                    f"Documento de {word_count} palabras analizado"
                ],
                "debilidades": [],
                "asunciones_no_probadas": [],
                "nivel_confianza": "No disponible (modo offline)",
                "preguntas": ["¿El argumento cita jurisprudencia relevante?"],
                "precedentes": [],
                "analisis_completo": (
                    "Análisis offline (LLM no disponible).\n\n"
                    f"📊 Métricas básicas:\n"
                    f"• Palabras: {word_count}\n"
                    f"• Cita normas: {'✅' if tiene_normas else '❌'}\n"
                    f"• Incluye fechas: {'✅' if tiene_fechas else '❌'}\n"
                    f"• Tiene pretensiones: {'✅' if tiene_pretensiones else '❌'}\n"
                    f"• Menciona pruebas: {'✅' if tiene_pruebas else '❌'}\n"
                    f"• Fundamentos legales: {'✅' if tiene_fundamentos else '❌'}\n\n"
                    "Para un análisis completo, conecta un proveedor LLM "
                    "(Ollama, Gemini, Claude u OpenAI)."
                ),
            }
        else:
            return {
                "puntos_debiles_explotables": [],
                "estrategia_ataque": [],
                "argumentos_replica": [],
                "vacios_probatorios": [],
                "inconsistencias": [],
                "jurisprudencia_contraria": [],
                "analisis_completo": (
                    "Análisis offline (LLM no disponible).\n\n"
                    f"📊 Métricas básicas del documento:\n"
                    f"• Palabras: {word_count}\n"
                    f"• Fundamento legal: {'✅' if tiene_fundamentos else '❌'}\n"
                    f"• Estructura: {'✅' if tiene_pretensiones else '⚠️ Sin pretensiones claras'}\n\n"
                    "Para un análisis adversarial completo, conecta un proveedor LLM."
                ),
            }

    def _format_response(self, analysis: Dict[str, Any], perspective_name: str) -> str:
        """Formatea el análisis para respuesta al usuario."""
        texto = analysis.get("analisis_completo", "")

        if not texto:
            return f"Análisis desde perspectiva '{perspective_name}' completado."

        return f"⚖️ Análisis: {perspective_name}\n\n{texto}"


# Instancia global
adversarial_analyzer = AdversarialAnalyzer()
