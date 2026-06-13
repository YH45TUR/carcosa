"""
Sistema Legal CO - Generador de Diagramas Legales
Genera diagramas Mermaid para visualización legal.

Tipos:
- timeline: Línea de tiempo procesal
- flowchart: Árbol de decisión jurídica
- graph: Mapa de partes del proceso
"""
from typing import Optional, Dict, Any, List
from datetime import datetime


class DiagramGenerator:
    """
    Genera diagramas Mermaid para visualización legal colombiana.
    """

    async def generate(
        self,
        tipo: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Genera un diagrama Mermaid.

        Args:
            tipo: Tipo de diagrama (timeline, flowchart, graph)
            data: Datos para el diagrama

        Returns:
            Código Mermaid + metadatos
        """
        generadores = {
            "timeline": self._generate_timeline,
            "flowchart": self._generate_flowchart,
            "graph": self._generate_graph,
        }

        if tipo not in generadores:
            raise ValueError(f"Tipo no soportado: {tipo}. Opciones: {list(generadores.keys())}")

        mermaid_code = await generadores[tipo](data)

        return {
            "chart": mermaid_code,
            "type": tipo,
            "title": data.get("title", f"Diagrama {tipo}"),
        }

    async def generate_from_case(
        self,
        case_data: Dict[str, Any],
        tipo: str = "timeline",
    ) -> Dict[str, Any]:
        """
        Genera diagrama automáticamente desde datos de un caso.

        Args:
            case_data: Datos del caso con timeline, partes, etc.
            tipo: Tipo de diagrama

        Returns:
            Código Mermaid
        """
        return await self.generate(tipo, case_data)

    async def _generate_timeline(self, data: Dict) -> str:
        """Genera diagrama de línea de tiempo procesal."""
        events = data.get("events", data.get("timeline", []))
        title = data.get("title", "Línea de Tiempo Procesal")

        lines = [
            "---",
            "title: " + title,
            "---",
            "timeline",
        ]

        # Agrupar eventos por fecha
        por_fecha = {}
        for event in events:
            fecha = event.get("fecha", event.get("date", ""))
            if isinstance(fecha, datetime):
                fecha = fecha.strftime("%Y-%m-%d")
            titulo = event.get("titulo", event.get("title", "Evento"))
            desc = event.get("descripcion", event.get("description", ""))

            if fecha not in por_fecha:
                por_fecha[fecha] = []
            por_fecha[fecha].append((titulo, desc))

        for fecha in sorted(por_fecha.keys()):
            items = por_fecha[fecha]
            if not items:
                continue
            first_title, first_desc = items[0]
            line = f"    {fecha} : {first_title}"
            if first_desc:
                line += f" : {first_desc[:80]}"
            lines.append(line)
            for titulo, desc in items[1:]:
                line = f"    {fecha} : {titulo}"
                if desc:
                    line += f" : {desc[:80]}"
                lines.append(line)

        return "\n".join(lines)

    async def _generate_flowchart(self, data: Dict) -> str:
        """Genera diagrama de flujo / árbol de decisión jurídico."""
        title = data.get("title", "Árbol de Decisión Jurídica")
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        lines = [
            "---",
            "title: " + title,
            "---",
            "flowchart TD",
        ]

        # Nodos
        for node in nodes:
            node_id = node.get("id", f"n{len(lines)}")
            label = node.get("label", node.get("text", ""))
            shape = node.get("shape", "rect")
            if shape == "decision":
                lines.append(f"    {node_id}{{{{{label}}}}}")
            elif shape == "start":
                lines.append(f"    {node_id}([{label}])")
            elif shape == "end":
                lines.append(f"    {node_id}([{label}])")
            elif shape == "process":
                lines.append(f"    {node_id}[{label}]")
            else:
                lines.append(f"    {node_id}[{label}]")

        # Conexiones
        for edge in edges:
            src = edge.get("from", edge.get("source", ""))
            dst = edge.get("to", edge.get("target", ""))
            label = edge.get("label", "")
            if label:
                lines.append(f"    {src} -->|{label}| {dst}")
            else:
                lines.append(f"    {src} --> {dst}")

        return "\n".join(lines)

    async def _generate_graph(self, data: Dict) -> str:
        """Genera mapa de partes del proceso (graph)."""
        title = data.get("title", "Mapa de Partes del Proceso")
        partes = data.get("partes", data.get("nodes", []))

        lines = [
            "---",
            "title: " + title,
            "---",
            "graph LR",
        ]

        roles_vistos = set()
        for parte in partes:
            nombre = parte.get("nombre", parte.get("label", ""))
            rol = parte.get("rol", parte.get("type", "parte"))

            if rol not in roles_vistos:
                lines.append(f"    subgraph {rol.capitalize()}")
                roles_vistos.add(rol)
                # Cerrar subgraph después
                lines.append(f"    end")
                # Insertar nodo antes del end
                idx = len(lines) - 1
                lines.insert(idx, f"        {rol}[{rol.capitalize()}]")

        # Conexiones entre partes
        for parte in partes:
            nombre = parte.get("nombre", "")
            rol = parte.get("rol", "parte")
            conexiones = parte.get("conexiones", parte.get("edges", []))
            for conn in conexiones:
                target = conn.get("con", conn.get("target", ""))
                tipo_rel = conn.get("tipo", conn.get("label", "relacionado"))
                lines.append(f"    {nombre} -->|{tipo_rel}| {target}")

        return "\n".join(lines)
