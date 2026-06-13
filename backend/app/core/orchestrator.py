"""
Sistema Legal CO - Orquestador
Router de intenciones que dirige mensajes al módulo correcto.
"""
from typing import Optional, Dict, Any
import re


class Router:
    """
    Orquestador central - detecta intención del usuario y deriva al módulo correcto.
    """
    
    # Palabras clave por módulo
    INTENT_PATTERNS = {
        "drafting": [
            "generar", "redactar", "escribir", "crear documento",
            "demanda", "tutela", "recurso", "derecho de petición",
            "contestación", "memorial", "poder", "escribo"
        ],
        "extraction": [
            "extraer", "procesar", "analizar documento", "metadatos",
            "radicado", "partes", "fechas", "normas", "cuantía"
        ],
        "audit": [
            "auditar", "revisar", "control calidad", "hallazgos",
            "nulidad", "término", "prescripción", "caducidad"
        ],
        "testimony": [
            "testimonio", "declaración", "contradictorio", "contradicción"
        ],
        "adversarial": [
            "juez", "contra parte", "adversario", "analizar perspectiva",
            "ojo del juez", "puntos débiles", "estrategia"
        ],
        "jurisprudence": [
            "jurisprudencia", "sentencia", "precedente", "corte",
            "buscar", "caso similar", "altas cortes"
        ],
        "diagram": [
            "diagrama", "flujo", "línea de tiempo", "mapa", "árbol"
        ],
        "calculator": [
            "calcular", "término", "vencimiento", "caduca", "prescribe",
            "días hábiles", "fecha límite"
        ],
        "timeline": [
            "cronología", "timeline", "historial", "secuencia", "resumen"
        ],
        "redteam": [
            "verificar", "citaciones", "alucinaciones", "revisar calidad"
        ]
    }
    
    async def detect_intent(self, message: str) -> str:
        """
        Detecta la intención del mensaje.
        Returns: nombre del módulo a usar.
        """
        message_lower = message.lower()
        
        # Buscar coincidencia
        for module, keywords in self.INTENT_PATTERNS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return module
        
        # Default: chat general
        return "chat"
    
    async def route_message(
        self,
        message: str,
        module: str,
        case_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Envía el mensaje al módulo correspondiente.
        """
        handlers = {
            "drafting": self._handle_drafting,
            "extraction": self._handle_extraction,
            "audit": self._handle_audit,
            "testimony": self._handle_testimony,
            "adversarial": self._handle_adversarial,
            "jurisprudence": self._handle_jurisprudence,
            "diagram": self._handle_diagram,
            "calculator": self._handle_calculator,
            "timeline": self._handle_timeline,
            "redteam": self._handle_redteam,
            "chat": self._handle_chat,
        }
        
        handler = handlers.get(module, self._handle_chat)
        return await handler(message, case_id)
    
    # === HANDLERS ===
    
    async def _handle_drafting(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        """Maneja solicitudes de redacción de documentos legales."""
        from app.modules.drafting.generator import DraftingGenerator
        from app.models.case import Case
        from app.db.database import SessionLocal

        generator = DraftingGenerator()

        # Obtener datos del caso si existe
        case_data = None
        if case_id:
            db = SessionLocal()
            try:
                case = db.query(Case).filter(Case.id == case_id).first()
                if case:
                    case_data = {
                        "demandante": case.cliente,
                        "demandado": case.demandado,
                        "juzgado": case.juzgado,
                        "radicado": case.radicado,
                    }
            finally:
                db.close()

        result = await generator.generate(
            message=message,
            case_id=case_id,
            case_data=case_data,
        )

        return {
            "response": result.get("response", "Error al generar documento"),
            "module": "drafting",
            "data": result.get("data"),
        }
    
    async def _handle_extraction(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        """Maneja solicitudes de extracción de metadatos de documentos."""
        from app.modules.extraction.batch_processor import BatchProcessor
        from app.models.case import CaseDocument
        from app.db.database import SessionLocal

        if not case_id:
            return {
                "response": "Por favor, especifica un caso para procesar sus documentos.",
                "module": "extraction",
            }

        db = SessionLocal()
        try:
            documents = db.query(CaseDocument).filter(
                CaseDocument.case_id == case_id
            ).all()

            if not documents:
                return {
                    "response": f"No hay documentos subidos en el caso #{case_id}. Sube documentos primero.",
                    "module": "extraction",
                }

            processor = BatchProcessor()
            file_paths = [doc.file_path for doc in documents if doc.file_path]

            if not file_paths:
                return {
                    "response": "Los documentos del caso no tienen archivos asociados.",
                    "module": "extraction",
                }

            results = await processor.process_batch(
                file_paths=file_paths,
                chunk_strategy="by_size",
                enable_ner=True,
            )

            # Resumir resultados
            completed = [r for r in results if r.get("status") == "completed"]
            errors = [r for r in results if r.get("status") == "error"]

            total_entities = sum(
                r.get("entities", {}).get("total_entities", 0)
                for r in completed
            )

            return {
                "response": (
                    f"Procesados {len(completed)} de {len(results)} documentos.\n"
                    f"Entidades encontradas: {total_entities}\n"
                    f"Errores: {len(errors)}"
                ),
                "module": "extraction",
                "data": {
                    "total": len(results),
                    "completed": len(completed),
                    "errors": len(errors),
                    "total_entities": total_entities,
                    "results": results,
                },
            }
        finally:
            db.close()
    
    async def _handle_audit(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        """Maneja solicitudes de auditoría legal."""
        from app.modules.audit.auditor import LegalAuditor
        from app.models.case import Case
        from app.db.database import SessionLocal

        auditor = LegalAuditor()

        # Obtener texto de documentos del caso si existe
        documents_text = None
        if case_id:
            db = SessionLocal()
            try:
                case = db.query(Case).filter(Case.id == case_id).first()
                if case and case.documents:
                    texts = []
                    for doc in case.documents:
                        if doc.extracted_text:
                            texts.append(f"--- {doc.original_filename} ---\n{doc.extracted_text[:3000]}")
                    if texts:
                        documents_text = "\n\n".join(texts)
            finally:
                db.close()

        result = await auditor.audit_case(
            case_id=case_id,
            message=message,
            document_text=documents_text,
        )

        return {
            "response": result.get("response", "Auditoría completada"),
            "module": "audit",
            "data": result.get("data"),
        }
    
    async def _handle_testimony(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        """Maneja solicitudes de análisis de testimonios."""
        from app.modules.testimony.analyzer import TestimonyAnalyzer

        analyzer = TestimonyAnalyzer()
        result = await analyzer.analyze(message)

        return {
            "response": result.get("resumen", "Análisis de testimonios completado."),
            "module": "testimony",
            "data": result,
        }
    
    async def _handle_adversarial(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        """Maneja solicitudes de análisis adversarial."""
        from app.modules.adversarial.analyzer import AdversarialAnalyzer

        # Detectar perspectiva
        perspective = "judge"
        message_lower = message.lower()
        if any(kw in message_lower for kw in ["contra-parte", "contraparte", "oponente", "adversario"]):
            perspective = "opponent"
        elif any(kw in message_lower for kw in ["ambos", "las dos", "completo"]):
            # Análisis completo desde ambas perspectivas
            analyzer = AdversarialAnalyzer()
            result = await analyzer.analyze_both(document_text=message)
            return {
                "response": result.get("response", "Análisis adversarial completo."),
                "module": "adversarial",
                "data": result.get("data"),
            }

        analyzer = AdversarialAnalyzer()
        result = await analyzer.analyze(
            document_text=message,
            perspective=perspective,
        )

        return {
            "response": result.get("response", "Análisis adversarial completado."),
            "module": "adversarial",
            "data": result.get("data"),
        }
    
    async def _handle_jurisprudence(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        from app.modules.jurisprudence.searcher import JurisprudenceSearcher
        searcher = JurisprudenceSearcher()
        return await searcher.search(message)
    
    async def _handle_diagram(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        return {"response": "Generación de diagramas: ¿qué tipo de diagrama necesitas?"}
    
    async def _handle_calculator(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        return {"response": "Calculadora de términos: ¿qué término procesal necesitas calcular?"}
    
    async def _handle_timeline(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        return {"response": "Generando timeline del caso..."}
    
    async def _handle_redteam(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        return {"response": "Verificación de calidad: analizando documento..."}
    
    async def _handle_chat(self, message: str, case_id: Optional[int]) -> Dict[str, Any]:
        from app.core.llm import LLMClient
        llm = LLMClient()
        response = await llm.chat(message, case_id)
        return {"response": response}