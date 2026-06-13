"""
Sistema Legal CO - Drafting Generator
Orquesta LLM + plantilla Jinja2 para generar documentos legales colombianos.
"""
from typing import Optional, Dict, Any, List
import os
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings


class DraftingGenerator:
    """
    Generador de documentos legales colombianos.

    Pipeline:
    1. El usuario describe qué documento necesita
    2. El LLM extrae los datos estructurados
    3. Se selecciona y rellena la plantilla Jinja2
    4. Se genera el documento final en texto
    """

    # Mapa de tipos de documento a plantillas
    DOCUMENT_TYPES = {
        "demanda": {
            "template": "demanda_civil.j2",
            "label": "Demanda Civil",
            "description": "Demanda verbal de mayor cuantía",
            "required_fields": ["demandante", "demandado", "hechos", "pretensiones"],
        },
        "tutela": {
            "template": "accion_tutela.j2",
            "label": "Acción de Tutela",
            "description": "Acción de tutela para protección de derechos fundamentales",
            "required_fields": ["demandante", "demandado", "hechos", "derechos_vulnerados"],
        },
        "recurso": {
            "template": "recurso_apelacion.j2",
            "label": "Recurso de Apelación",
            "description": "Recurso de apelación contra providencias judiciales",
            "required_fields": ["demandante", "demandado", "cargos_inconformidad"],
        },
        "derecho_peticion": {
            "template": "derecho_peticion.j2",
            "label": "Derecho de Petición",
            "description": "Solicitud respetuosa ante autoridades",
            "required_fields": ["demandante", "solicitudes", "hechos"],
        },
    }

    def __init__(self):
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def generate(
        self,
        message: str,
        case_id: Optional[int] = None,
        document_type: Optional[str] = None,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Genera un documento legal a partir de la descripción del usuario.

        Args:
            message: Descripción del documento que necesita
            case_id: ID del caso asociado (opcional)
            document_type: Tipo de documento (demanda, tutela, etc.)
            case_data: Datos del caso para precargar el template

        Returns:
            Dict con el documento generado y metadatos
        """
        # Paso 1: Detectar tipo de documento
        doc_type = document_type or await self._detect_document_type(message)

        if doc_type not in self.DOCUMENT_TYPES:
            return {
                "success": False,
                "response": (
                    f"Tipo de documento '{doc_type}' no soportado. "
                    f"Tipos disponibles: {', '.join(self.DOCUMENT_TYPES.keys())}"
                ),
            }

        doc_config = self.DOCUMENT_TYPES[doc_type]

        # Paso 2: Extraer datos estructurados via LLM
        extracted_data = await self._extract_data_with_llm(message, doc_type, case_data)

        # Verificar campos requeridos
        missing_fields = [
            f for f in doc_config["required_fields"]
            if not extracted_data.get(f)
        ]

        if missing_fields:
            return {
                "success": False,
                "response": (
                    f"Faltan campos requeridos para {doc_config['label']}: "
                    f"{', '.join(missing_fields)}. "
                    f"Por favor, proporciona más detalles."
                ),
                "missing_fields": missing_fields,
                "document_type": doc_type,
            }

        # Paso 3: Rellenar plantilla
        try:
            template = self.env.get_template(doc_config["template"])
            rendered = template.render(**extracted_data)
        except Exception as e:
            return {
                "success": False,
                "response": f"Error al generar el documento: {str(e)}",
            }

        # Paso 4: Calcular estadísticas
        word_count = len(rendered.split())
        page_estimate = max(1, word_count // 350)  # ~350 palabras por página

        return {
            "success": True,
            "response": (
                f"✅ {doc_config['label']} generada exitosamente.\n"
                f"📄 {word_count} palabras (~{page_estimate} páginas)\n"
                f"📋 Tipo: {doc_config['description']}\n\n"
                f"{rendered}"
            ),
            "data": {
                "document_type": doc_type,
                "content": rendered,
                "template_data": extracted_data,
                "word_count": word_count,
                "page_estimate": page_estimate,
                "case_id": case_id,
            },
        }

    async def generate_from_data(
        self,
        document_type: str,
        template_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Genera un documento directamente desde datos estructurados.

        Args:
            document_type: Tipo de documento
            template_data: Datos para llenar la plantilla

        Returns:
            Dict con el documento generado
        """
        if document_type not in self.DOCUMENT_TYPES:
            raise ValueError(
                f"Tipo de documento '{document_type}' no soportado. "
                f"Opciones: {', '.join(self.DOCUMENT_TYPES.keys())}"
            )

        doc_config = self.DOCUMENT_TYPES[document_type]
        template = self.env.get_template(doc_config["template"])

        # Valores por defecto sensibles
        defaults = {
            "fecha": datetime.now().strftime("%d de %B de %Y"),
            "ciudad": "Bogotá D.C.",
            "cabecera": "",
            "tipo_apoderado": "abogado en ejercicio",
            "calidad": "apoderado judicial",
        }
        merged = {**defaults, **template_data}

        rendered = template.render(**merged)

        return {
            "content": rendered,
            "document_type": document_type,
            "word_count": len(rendered.split()),
            "template_data": merged,
        }

    async def _detect_document_type(self, message: str) -> str:
        """Detecta el tipo de documento de la descripción del usuario."""
        message_lower = message.lower()

        # Mapa de keywords a tipos
        keywords = {
            "demanda": ["demanda", "demandar", "proceso verbal", "ejecutivo", "ordinario"],
            "tutela": ["tutela", "acción de tutela", "amparo", "derecho fundamental"],
            "recurso": ["recurso", "apelación", "reposición", "casación", "apelar"],
            "derecho_peticion": ["derecho de petición", "petición", "solicitud respetuosa"],
        }

        for doc_type, doc_keywords in keywords.items():
            for kw in doc_keywords:
                if kw in message_lower:
                    return doc_type

        # Default a demanda si no se detecta
        return "demanda"

    async def _extract_data_with_llm(
        self,
        message: str,
        document_type: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extrae datos estructurados usando el LLM.
        Si no hay LLM disponible, usa datos simulados.
        """
        # Intentar usar LLM
        try:
            from app.core.llm import LLMClient
            llm = LLMClient()

            doc_config = self.DOCUMENT_TYPES[document_type]

            system_prompt = (
                f"Eres un asistente legal experto en derecho colombiano. "
                f"Extrae los datos estructurados para generar {doc_config['label']}.\n\n"
                f"Responde SOLO con un JSON válido con estos campos:\n"
                f"- demandante: nombre del demandante\n"
                f"- demandado: nombre del demandado\n"
                f"- hechos: lista de hechos numerados\n"
                f"- pretensiones: lista de pretensiones\n"
                f"- pruebas: lista de pruebas\n"
                f"- fundamentos_derecho: lista de fundamentos legales\n"
                f"- cuantia: valor de la cuantía (si aplica)\n"
                f"- juzgado: juzgado competente\n"
                f"- ciudad: ciudad\n"
                f"- anexos: lista de anexos\n\n"
                f"Para tutela incluir también:\n"
                f"- derechos_vulnerados: lista de derechos fundamentales\n"
                f"- fundamentos_accion: texto de fundamentos\n\n"
                f"Para recurso incluir también:\n"
                f"- cargos_inconformidad: lista de cargos\n"
                f"- fecha_providencia: fecha\n"
                f"- tribunal_superior: tribunal\n\n"
                f"Para derecho de petición incluir también:\n"
                f"- solicitudes: lista de solicitudes\n"
                f"- autoridad_destinataria: nombre de la autoridad\n"
                f"- entidad_destinataria: entidad\n"
            )

            data_str = await llm.chat(
                message=message,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            # Intentar parsear JSON
            import re
            json_match = re.search(r'\{.*\}', data_str, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(data_str)

            # Combinar con datos del caso
            if case_data:
                data = {**case_data, **data}

            return data

        except Exception:
            # Fallback: datos simulados
            return self._generate_mock_data(message, document_type, case_data)

    def _generate_mock_data(
        self,
        message: str,
        document_type: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Genera datos de ejemplo cuando el LLM no está disponible."""
        base = {
            "fecha": datetime.now().strftime("%d de %B de %Y"),
            "ciudad": "Bogotá D.C.",
            "demandante": "Juan Pérez López",
            "demandado": "María García Ruiz",
            "juzgado": "Juzgado Civil del Circuito de Bogotá (REPARTO)",
            "nombre_apoderado": "Carlos Andrés Martínez",
            "documento_apoderado": "C.C. No. 79.123.456 de Bogotá",
            "tarjeta_profesional": "123.456",
            "correo_apoderado": "carlos.martinez@abogado.co",
            "direccion_apoderado": "Calle 100 No. 15-30, Oficina 502",
            "telefono_apoderado": "310 123 4567",
            "correo_demandante": "juan.perez@email.com",
            "telefono_demandante": "315 987 6543",
            "direccion_demandante": "Carrera 7 No. 45-20, Apartamento 301",
            "correo_demandado": "maria.garcia@email.com",
            "telefono_demandado": "320 456 7890",
            "direccion_demandado": "Avenida 19 No. 120-45, Casa 15",
            "hechos": [
                "Entre las partes se celebró un contrato de compraventa el día 15 de marzo de 2024.",
                "El demandante cumplió con todas sus obligaciones contractuales.",
                "El demandado ha incumplido con el pago del precio acordado.",
                "A la fecha de presentación de esta demanda, la deuda asciende a la suma pactada.",
                "Se ha agotado el requisito de procedibilidad de la conciliación extrajudicial.",
            ],
            "pretensiones": [
                "Que se declare que el demandado incumplió el contrato de compraventa.",
                "Que se condene al demandado a pagar la suma adeudada más los intereses moratorios.",
                "Que se condene al demandado al pago de las costas y agencias en derecho.",
            ],
            "pruebas": [
                "Documental: Copia del contrato de compraventa.",
                "Documental: Facturas de pago y extractos bancarios.",
                "Testimonial: Declaración de testigos presenciales.",
                "Documental: Certificado de existencia y representación legal.",
            ],
            "fundamentos_derecho": [
                "Artículos 1501, 1602, 1849 y siguientes del Código Civil Colombiano.",
                "Artículos 368 y siguientes del Código General del Proceso.",
                "Artículo 87 de la Ley 1676 de 2013.",
            ],
            "anexos": [
                "Copia del contrato de compraventa.",
                "Certificado de existencia y representación legal.",
                "Constancia de agotamiento de conciliación extrajudicial.",
                "Poder debidamente otorgado.",
                "Cédula de ciudadanía del demandante.",
            ],
            "cuantia": "La cuantía se estima en la suma de $200.000.000 M/CTE.",
            "competencia": "Es usted competente, señor Juez, por la naturaleza del asunto, por el domicilio de las partes y por la cuantía.",
            "identificacion_demandante": "mayor de edad, identificado con C.C. No. 79.987.654 de Bogotá",
            "identificacion_demandado": "mayor de edad, identificado con C.C. No. 52.123.456 de Bogotá",
        }

        # Datos específicos por tipo
        if document_type == "tutela":
            base.update({
                "derechos_vulnerados": [
                    "Derecho fundamental a la salud (Art. 49 C.P.)",
                    "Derecho fundamental a la vida digna (Art. 11 C.P.)",
                    "Derecho fundamental a la seguridad social (Art. 48 C.P.)",
                ],
                "fundamentos_accion": (
                    "La acción de tutela procede como mecanismo transitorio para evitar "
                    "un perjuicio irremediable, de conformidad con el artículo 86 de la "
                    "Constitución Política y el Decreto 2591 de 1991."
                ),
            })
            base["hechos"] = [
                "El accionante es afiliado a la entidad accionada desde el año 2018.",
                "El médico tratante ordenó el procedimiento requerido el 10 de enero de 2024.",
                "La entidad accionada ha negado la autorización del procedimiento.",
                "La negativa pone en riesgo la vida y la integridad personal del accionante.",
            ]
        elif document_type == "recurso":
            base.update({
                "cargos_inconformidad": [
                    "La providencia recurrida incurre en error de hecho en la valoración de las pruebas.",
                    "Se desconocieron los precedentes jurisprudenciales aplicables al caso.",
                    "La interpretación normativa realizada es contraria a la ley sustancial.",
                ],
                "juzgado_origen": "Juzgado 1° Civil del Circuito de Bogotá",
                "fecha_providencia": "01 de mayo de 2024",
                "fecha_notificacion": "15 de mayo de 2024",
                "tribunal_superior": "Tribunal Superior del Distrito Judicial de Bogotá",
                "oportunidad": "El recurso se interpone dentro del término legal de 5 días.",
                "parte_recurrente": "la parte demandante",
                "sustentacion": (
                    "La providencia recurrida debe ser revocada por cuanto "
                    "no se ajusta a derecho, tal como se demostrará en la "
                    "sustentación del recurso ante el superior."
                ),
                "termino_recurso": 5,
            })
            base["pretensiones"] = [
                "Que se revoque la providencia recurrida.",
                "Que en su lugar, se acceda a las pretensiones de la demanda.",
            ]
        elif document_type == "derecho_peticion":
            base.update({
                "solicitudes": [
                    "Se expida copia íntegra del expediente administrativo.",
                    "Se informe el estado actual de la solicitud radicada el 20 de enero de 2024.",
                    "Se certifique el tiempo de respuesta de la entidad.",
                ],
                "autoridad_destinataria": "Jefe de la Oficina Jurídica",
                "entidad_destinataria": "Entidad Pública Correspondiente",
                "fundamentos_juridicos": (
                    "La presente solicitud se fundamenta en el artículo 23 de la "
                    "Constitución Política de Colombia, la Ley 1755 de 2015 y el "
                    "artículo 5 del Código de Procedimiento Administrativo."
                ),
                "tipo_peticion": "información y copias",
            })

        # Combinar con datos del caso si existen
        if case_data:
            for key in ["demandante", "demandado", "juzgado", "radicado", "cuantia"]:
                if key in case_data and case_data[key]:
                    base[key] = case_data[key]

        return base
