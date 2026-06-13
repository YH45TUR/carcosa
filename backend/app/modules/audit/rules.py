"""
Sistema Legal CO - Reglas de Auditoría Legal
Sistema de hallazgos con reglas de verificación contra códigos procesales colombianos.

Códigos soportados:
- CGP: Código General del Proceso (Ley 1564 de 2012)
- CPACA: Código de Procedimiento Administrativo (Ley 1437 de 2011)
- CPP: Código de Procedimiento Penal (Ley 906 de 2004)
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta


class Criticidad(str, Enum):
    """Nivel de criticidad del hallazgo."""
    CRITICO = "crítico"
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"


class Categoria(str, Enum):
    """Categoría del hallazgo."""
    NULIDAD = "nulidad_procesal"
    TERMINOS = "terminos_vencidos"
    LEGITIMACION = "falta_legitimacion"
    PRETENSIONES = "errores_pretensiones"
    PRUEBAS = "pruebas_inadmisibles"
    INCONSISTENCIAS = "inconsistencias_hechos"
    CITAS = "citas_desactualizadas"
    FORMA = "errores_forma"
    COMPETENCIA = "falta_competencia"
    NOTIFICACIONES = "notificaciones_irregulares"
    CUANTIA = "cuantia_incorrecta"


@dataclass
class Hallazgo:
    """Hallazgo individual de la auditoría."""
    criticidad: Criticidad
    categoria: Categoria
    titulo: str
    descripcion: str
    norma: str
    sugerencia: str
    ubicacion: Optional[str] = None
    codigo: Optional[str] = None  # Código del artículo
    automatizable: bool = False  # Si puede detectarse automáticamente


@dataclass
class ResultadoAuditoria:
    """Resultado completo de la auditoría."""
    hallazgos: List[Hallazgo] = field(default_factory=list)
    total_hallazgos: int = 0
    criticos: int = 0
    altos: int = 0
    medios: int = 0
    bajos: int = 0
    fecha: str = field(default_factory=lambda: datetime.now().isoformat())
    resumen: str = ""

    def add(self, hallazgo: Hallazgo):
        """Agrega un hallazgo y actualiza contadores."""
        self.hallazgos.append(hallazgo)
        self.total_hallazgos += 1

        if hallazgo.criticidad == Criticidad.CRITICO:
            self.criticos += 1
        elif hallazgo.criticidad == Criticidad.ALTO:
            self.altos += 1
        elif hallazgo.criticidad == Criticidad.MEDIO:
            self.medios += 1
        elif hallazgo.criticidad == Criticidad.BAJO:
            self.bajos += 1

    def generar_resumen(self) -> str:
        """Genera un resumen ejecutivo de la auditoría."""
        lines = [
            f"📋 Auditoría Legal — {self.fecha[:10]}",
            f"",
            f"Hallazgos: {self.total_hallazgos} total",
            f"  🔴 Críticos: {self.criticos}",
            f"  🟠 Altos: {self.altos}",
            f"  🟡 Medios: {self.medios}",
            f"  🟢 Bajos: {self.bajos}",
            f"",
        ]

        if self.hallazgos:
            lines.append("Detalle:")
            for h in self.hallazgos:
                icon = {"crítico": "🔴", "alto": "🟠", "medio": "🟡", "bajo": "🟢"}
                lines.append(
                    f"  {icon.get(h.criticidad.value, '⚪')} [{h.criticidad.value.upper()}] "
                    f"{h.titulo}"
                )
                lines.append(f"     {h.descripcion[:200]}")
                if h.norma:
                    lines.append(f"     📜 {h.norma}")
                lines.append("")

        self.resumen = "\n".join(lines)
        return self.resumen


class ReglasAuditoria:
    """
    Banco de reglas de auditoría legal colombiana.
    Cada regla puede verificar un aspecto del documento y generar hallazgos.
    """

    # ==========================================
    # CGP - Código General del Proceso (Ley 1564/2012)
    # ==========================================

    REGLAS_CGP: List[Hallazgo] = [
        Hallazgo(
            criticidad=Criticidad.CRITICO,
            categoria=Categoria.NULIDAD,
            titulo="Falta de notificación del auto admisorio",
            descripcion="La no notificación en debida forma del auto que admite la demanda "
                        "constituye nulidad insaneable (Art. 133-8 CGP)",
            norma="Artículo 133, numeral 8 del Código General del Proceso (Ley 1564 de 2012)",
            sugerencia="Verificar que todas las partes hayan sido notificadas personalmente "
                       "o por estado dentro del término legal",
            codigo="CGP-133-8",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.CRITICO,
            categoria=Categoria.TERMINOS,
            titulo="Término de traslado de la demanda vencido",
            descripcion="El término de traslado de la demanda es de 20 días hábiles "
                        "para procesos verbales (Art. 369 CGP)",
            norma="Artículo 369 del Código General del Proceso",
            sugerencia="Verificar que el demandado haya contestado dentro del término "
                       "o declararlo en rebeldía",
            codigo="CGP-369",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.ALTO,
            categoria=Categoria.PRETENSIONES,
            titulo="Acumulación indebida de pretensiones",
            descripcion="Las pretensiones acumuladas deben cumplir con los requisitos "
                        "del Art. 88 CGP: mismo juez, mismas partes, mismas vías procesales",
            norma="Artículo 88 del Código General del Proceso",
            sugerencia="Revisar que todas las pretensiones puedan tramitarse por el mismo proceso",
            codigo="CGP-88",
            automatizable=False,
        ),
        Hallazgo(
            criticidad=Criticidad.MEDIO,
            categoria=Categoria.FORMA,
            titulo="Falta de juramento de la demanda",
            descripcion="Toda demanda debe presentarse con juramento de que no se "
                        "ha promovido otro proceso por las mismas pretensiones",
            norma="Artículo 82, numeral 10 del Código General del Proceso",
            sugerencia="Incluir la afirmación juramentada al final de la demanda",
            codigo="CGP-82-10",
            automatizable=True,
        ),
    ]

    # ==========================================
    # CPACA - Código de Procedimiento Administrativo (Ley 1437/2011)
    # ==========================================

    REGLAS_CPACA: List[Hallazgo] = [
        Hallazgo(
            criticidad=Criticidad.CRITICO,
            categoria=Categoria.TERMINOS,
            titulo="Caducidad de la acción de nulidad y restablecimiento",
            descripcion="La acción de nulidad y restablecimiento del derecho caduca "
                        "en 4 meses desde la notificación del acto (Art. 164 CPACA)",
            norma="Artículo 164, numeral 2, literal d del CPACA (Ley 1437 de 2011)",
            sugerencia="Verificar la fecha de notificación del acto demandado "
                       "y calcular el término de caducidad",
            codigo="CPACA-164-2d",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.ALTO,
            categoria=Categoria.PRETENSIONES,
            titulo="Omisión del requisito de conciliación prejudicial",
            descripcion="Para acudir a la jurisdicción contencioso administrativa "
                        "es requisito previo la conciliación extrajudicial",
            norma="Artículo 161 del CPACA (Ley 1437 de 2011)",
            sugerencia="Acreditar el agotamiento del requisito de conciliación "
                       "con la constancia respectiva",
            codigo="CPACA-161",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.CRITICO,
            categoria=Categoria.TERMINOS,
            titulo="Silencio administrativo negativo no configurado",
            descripcion="El silencio administrativo negativo se configura a los "
                        "3 meses de presentada la petición (Art. 83 CPACA)",
            norma="Artículo 83 del CPACA (Ley 1437 de 2011)",
            sugerencia="Verificar si han transcurrido los 3 meses desde la "
                       "presentación de la solicitud",
            codigo="CPACA-83",
            automatizable=True,
        ),
    ]

    # ==========================================
    # CPP - Código de Procedimiento Penal (Ley 906/2004)
    # ==========================================

    REGLAS_CPP: List[Hallazgo] = [
        Hallazgo(
            criticidad=Criticidad.CRITICO,
            categoria=Categoria.TERMINOS,
            titulo="Vencimiento del término de investigación",
            descripcion="La Fiscalía tiene hasta 2 años para formular imputación "
                        "en casos complejos (Art. 175 CPP)",
            norma="Artículo 175 del Código de Procedimiento Penal (Ley 906 de 2004)",
            sugerencia="Verificar si el término de investigación ha vencido "
                       "y solicitar preclusión si corresponde",
            codigo="CPP-175",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.ALTO,
            categoria=Categoria.PRUEBAS,
            titulo="Prueba de referencia no admisible",
            descripcion="No son admisibles pruebas de referencia para demostrar "
                        "el hecho punible (Art. 381 CPP)",
            norma="Artículo 381 del Código de Procedimiento Penal",
            sugerencia="Revisar que las pruebas no sean de referencia cuando "
                       "pretendan demostrar el hecho punible",
            codigo="CPP-381",
            automatizable=False,
        ),
    ]

    # ==========================================
    # Reglas generales de forma
    # ==========================================

    REGLAS_GENERALES: List[Hallazgo] = [
        Hallazgo(
            criticidad=Criticidad.BAJO,
            categoria=Categoria.FORMA,
            titulo="Formato NTC 1486",
            descripcion="El documento debe seguir la Norma Técnica Colombiana 1486 "
                        "para presentación de trabajos escritos",
            norma="NTC 1486 - ICONTEC",
            sugerencia="Usar Times New Roman 12pt, interlineado 1.5, "
                       "márgenes superior 3cm, izquierda 4cm, derecha 2cm, inferior 3cm",
            codigo="NTC-1486",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.MEDIO,
            categoria=Categoria.CITAS,
            titulo="Cita normativa sin año de expedición",
            descripcion="Las citas de leyes y decretos deben incluir el año "
                        "de expedición para su correcta identificación",
            norma="Técnica legislativa colombiana - Ley 5 de 1992",
            sugerencia="Agregar el año a las citas normativas: Ley 100 de 1993, no Ley 100",
            codigo="CIT-001",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.MEDIO,
            categoria=Categoria.FORMA,
            titulo="Falta de tarjeta profesional en la firma",
            descripcion="Todo abogado debe incluir su número de Tarjeta Profesional "
                        "al firmar documentos judiciales",
            norma="Artículo 27 del Decreto 196 de 1971 (Estatuto del Abogado)",
            sugerencia="Incluir T.P. No. seguido del número de tarjeta profesional",
            codigo="EST-001",
            automatizable=True,
        ),
        Hallazgo(
            criticidad=Criticidad.BAJO,
            categoria=Categoria.FORMA,
            titulo="Numeración incorrecta de folios",
            descripcion="Los documentos judiciales deben presentarse con numeración "
                        "consecutiva de folios",
            norma="Acuerdo PSAA07-4000 de 2007 - CSJ",
            sugerencia="Numerar cada folio en la esquina superior derecha",
            codigo="FOL-001",
            automatizable=True,
        ),
    ]

    @classmethod
    def get_all_rules(cls) -> List[Hallazgo]:
        """Obtiene todas las reglas registradas."""
        return (
            cls.REGLAS_CGP +
            cls.REGLAS_CPACA +
            cls.REGLAS_CPP +
            cls.REGLAS_GENERALES
        )

    @classmethod
    def get_rules_by_code(cls, code: str) -> List[Hallazgo]:
        """Obtiene reglas por código procesal."""
        code_map = {
            "CGP": cls.REGLAS_CGP,
            "CPACA": cls.REGLAS_CPACA,
            "CPP": cls.REGLAS_CPP,
        }
        return code_map.get(code.upper(), [])

    @classmethod
    def get_rules_by_criticidad(cls, criticidad: Criticidad) -> List[Hallazgo]:
        """Obtiene reglas por nivel de criticidad."""
        return [r for r in cls.get_all_rules() if r.criticidad == criticidad]

    @classmethod
    def get_automatizable_rules(cls) -> List[Hallazgo]:
        """Obtiene reglas que pueden detectarse automáticamente."""
        return [r for r in cls.get_all_rules() if r.automatizable]

    @classmethod
    def validate_text(cls, text: str) -> List[Hallazgo]:
        """
        Valida un texto contra reglas automatizables.
        Retorna hallazgos basados en patrones detectables en el texto.
        """
        hallazgos = []
        text_lower = text.lower() if text else ""

        for regla in cls.get_automatizable_rules():
            # Validaciones por código
            if regla.codigo == "CGP-82-10":
                # Verificar si hay juramento
                if "juramento" not in text_lower:
                    hallazgos.append(regla)

            elif regla.codigo == "NTC-1486":
                # Verificar formato básico
                if len(text.split("\n")) < 5:
                    hallazgos.append(regla)

            elif regla.codigo == "CIT-001":
                # Verificar citas sin año
                import re
                citas_sin_anio = re.findall(r'\b(Ley|Decreto|Resolución)\s+\d+\b(?!\s*de\s*\d{4})', text)
                if citas_sin_anio:
                    hallazgos.append(regla)

            elif regla.codigo == "EST-001":
                # Verificar si hay T.P.
                if "t.p." not in text_lower and "tarjeta profesional" not in text_lower:
                    hallazgos.append(regla)

            elif regla.codigo == "CPACA-161":
                # Verificar conciliación
                if "conciliación" not in text_lower and "conciliacion" not in text_lower:
                    hallazgos.append(regla)

        return hallazgos
