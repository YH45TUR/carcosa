"""
Sistema Legal CO - Extractor de Timeline
Post-procesamiento de metadatos del caso para generar cronología ordenada y resumen ejecutivo.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


class TimelineExtractor:
    """
    Extrae y organiza eventos cronológicos de los metadatos de un caso.

    Pipeline:
    1. Extrae fechas del texto del caso
    2. Clasifica eventos por tipo
    3. Ordena cronológicamente
    4. Genera resumen ejecutivo
    """

    async def extract_from_case(
        self,
        case_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extrae timeline de los datos de un caso.

        Args:
            case_data: Datos del caso (documentos, metadatos, texto extraído)

        Returns:
            Timeline ordenado + resumen
        """
        events = []

        # Evento 1: Creación del caso
        if case_data.get("created_at"):
            events.append({
                "fecha": self._parse_fecha(case_data["created_at"]),
                "titulo": "Apertura del caso",
                "descripcion": f"Caso creado - Cliente: {case_data.get('cliente', 'N/A')}",
                "tipo": "apertura",
                "icon": "📁",
            })

        # Evento 2: Documentos subidos
        documents = case_data.get("documents", [])
        for doc in documents:
            if doc.get("created_at"):
                events.append({
                    "fecha": self._parse_fecha(doc["created_at"]),
                    "titulo": f"Documento subido: {doc.get('original_filename', 'documento')}",
                    "descripcion": f"Tipo: {doc.get('file_type', 'desconocido')} ({self._format_size(doc.get('file_size', 0))})",
                    "tipo": "documento",
                    "icon": "📄",
                    "documento_id": doc.get("id"),
                })

        # Evento 3: Versiones generadas
        versions = case_data.get("versions", [])
        for ver in versions:
            if ver.get("created_at"):
                events.append({
                    "fecha": self._parse_fecha(ver["created_at"]),
                    "titulo": f"Documento generado: {ver.get('document_type', 'documento')} v{ver.get('version_number', 1)}",
                    "descripcion": "Versión generada por el sistema",
                    "tipo": "version",
                    "icon": "✍️",
                })

        # Evento 4: Términos calculados
        terms = case_data.get("terms", [])
        for term in terms:
            if term.get("created_at"):
                events.append({
                    "fecha": self._parse_fecha(term["created_at"]),
                    "titulo": f"Término calculado: {term.get('tipo', 'procesal')}",
                    "descripcion": f"Norma: {term.get('norma', '')}",
                    "tipo": "termino",
                    "icon": "⏱️",
                })

        # Extraer fechas del texto del caso
        documento_texto = case_data.get("text", case_data.get("description", ""))
        if documento_texto:
            fechas_texto = self._extract_dates_from_text(documento_texto)
            for fecha_info in fechas_texto:
                events.append({
                    "fecha": fecha_info["fecha"],
                    "titulo": f"Fecha mencionada: {fecha_info['texto']}",
                    "descripcion": fecha_info.get("contexto", ""),
                    "tipo": "mencion",
                    "icon": "📅",
                })

        # Ordenar cronológicamente
        events.sort(key=lambda e: e.get("fecha", datetime.min))

        # Generar resumen
        resumen = self._generate_summary(events, case_data)

        return {
            "events": events,
            "total_events": len(events),
            "fecha_inicio": events[0]["fecha"].isoformat() if events else None,
            "fecha_fin": events[-1]["fecha"].isoformat() if events else None,
            "resumen": resumen,
        }

    async def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae timeline del texto de un documento legal.

        Args:
            text: Texto del documento

        Returns:
            Eventos ordenados con resumen
        """
        events = []
        fechas = self._extract_dates_from_text(text)

        for fecha_info in fechas:
            events.append({
                "fecha": fecha_info["fecha"],
                "titulo": fecha_info['texto'],
                "descripcion": fecha_info.get("contexto", ""),
                "tipo": "extraido",
                "icon": "📅",
            })

        events.sort(key=lambda e: e["fecha"])

        return {
            "events": events,
            "total_events": len(events),
            "resumen": self._generate_summary(events, {"text": text}),
        }

    def _extract_dates_from_text(self, text: str) -> List[Dict]:
        """Extrae fechas en formato colombiano del texto."""
        fechas = []
        pattern = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})'

        for match in re.finditer(pattern, text, re.IGNORECASE):
            dia, mes_str, año = match.groups()
            meses = {
                "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
            }
            mes = meses.get(mes_str.lower(), 1)
            try:
                fecha = datetime(int(año), mes, int(dia))
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                contexto = re.sub(r'\s+', ' ', text[start:end]).strip()

                fechas.append({
                    "fecha": fecha,
                    "texto": match.group(0),
                    "contexto": contexto[:200],
                })
            except ValueError:
                continue

        return fechas

    def _parse_fecha(self, fecha_val) -> datetime:
        """Convierte varios formatos de fecha a datetime."""
        if isinstance(fecha_val, datetime):
            return fecha_val
        if isinstance(fecha_val, str):
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(fecha_val, fmt)
                except ValueError:
                    continue
        return datetime.now()

    def _format_size(self, size: int) -> str:
        """Formatea tamaño de archivo."""
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def _generate_summary(self, events: List[Dict], case_data: Dict) -> str:
        """Genera resumen ejecutivo del timeline."""
        if not events:
            return "No hay eventos registrados para este caso."

        cliente = case_data.get("cliente", "el caso")
        lines = [
            f"📋 CRONOLOGÍA DEL CASO — {cliente}",
            f"",
            f"Período: {events[0]['fecha'].strftime('%d/%m/%Y')} → {events[-1]['fecha'].strftime('%d/%m/%Y')}",
            f"Total eventos: {len(events)}",
            f"",
        ]

        for event in events[:15]:  # Top 15
            fecha = event["fecha"].strftime("%d/%m/%Y")
            icon = event.get("icon", "•")
            lines.append(f"  {icon} {fecha} — {event['titulo']}")
            if event.get("descripcion"):
                lines.append(f"     {event['descripcion'][:100]}")
            lines.append("")

        if len(events) > 15:
            lines.append(f"... y {len(events) - 15} eventos más")

        return "\n".join(lines)
