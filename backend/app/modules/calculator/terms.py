"""
Sistema Legal CO - Calculadora de Términos Procesales
Cálculo de días hábiles, caducidad, prescripción y vencimiento de términos.

Códigos soportados:
- CGP: Código General del Proceso (Ley 1564/2012)
- CPACA: Código de Procedimiento Administrativo (Ley 1437/2011)
- CPP: Código de Procedimiento Penal (Ley 906/2004)
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import calendar


class TerminoProcesal:
    """Resultado del cálculo de un término procesal."""
    def __init__(
        self,
        tipo: str,
        codigo: str,
        fecha_inicio: date,
        fecha_fin: date,
        dias_habiles: int,
        dias_calendario: int,
        norma: str,
        alerta: Optional[str] = None,
    ):
        self.tipo = tipo
        self.codigo = codigo
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.dias_habiles = dias_habiles
        self.dias_calendario = dias_calendario
        self.norma = norma
        self.alerta = alerta

    @property
    def days_remaining(self) -> int:
        return (self.fecha_fin - date.today()).days

    @property
    def is_expired(self) -> bool:
        return self.days_remaining < 0

    @property
    def is_urgent(self) -> bool:
        return 0 <= self.days_remaining <= 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo,
            "codigo": self.codigo,
            "fecha_inicio": self.fecha_inicio.isoformat(),
            "fecha_fin": self.fecha_fin.isoformat(),
            "dias_habiles": self.dias_habiles,
            "dias_calendario": self.dias_calendario,
            "norma": self.norma,
            "days_remaining": self.days_remaining,
            "is_expired": self.is_expired,
            "is_urgent": self.is_urgent,
            "alerta": self.alerta or self._generar_alerta(),
        }

    def _generar_alerta(self) -> str:
        if self.is_expired:
            return f"🔴 VENCIDO — El término venció hace {abs(self.days_remaining)} días"
        elif self.is_urgent and self.days_remaining > 0:
            return f"⚠️ URGENTE — Vence en {self.days_remaining} días hábiles"
        else:
            return f"✅ Vigente — Vence en {self.days_remaining} días"


class CalculadoraTerminos:
    """
    Calculadora de términos procesales colombianos.

    Feriados colombianos fijos (Ley 51 de 1983, Ley 1059 de 2006):
    - 1 de enero (Año Nuevo)
    - 6 de enero (Reyes Magos - trasladable)
    - 19 de marzo (Día de San José - trasladable)
    - 1 de mayo (Día del Trabajo)
    - 29 de junio (San Pedro y San Pablo - trasladable)
    - 20 de julio (Independencia)
    - 7 de agosto (Batalla de Boyacá)
    - 15 de agosto (Asunción - trasladable)
    - 12 de octubre (Día de la Raza - trasladable)
    - 1 de noviembre (Todos los Santos - trasladable)
    - 11 de noviembre (Independencia Cartagena - trasladable)
    - 8 de diciembre (Inmaculada Concepción)
    - 25 de diciembre (Navidad)
    """

    FERIADOS_FIJOS = [
        (1, 1),    # Año Nuevo
        (5, 1),    # Día del Trabajo
        (7, 20),   # Independencia
        (8, 7),    # Batalla de Boyacá
        (12, 8),   # Inmaculada Concepción
        (12, 25),  # Navidad
    ]

    @staticmethod
    def es_dia_habil(fecha: date) -> bool:
        """Verifica si una fecha es día hábil en Colombia."""
        if fecha.weekday() >= 5:  # Sábado o domingo
            return False
        if (fecha.month, fecha.day) in CalculadoraTerminos.FERIADOS_FIJOS:
            return False
        return True

    @staticmethod
    def sumar_dias_habiles(desde: date, dias: int) -> date:
        """Suma días hábiles a una fecha."""
        actual = desde
        contador = 0
        while contador < dias:
            actual += timedelta(days=1)
            if CalculadoraTerminos.es_dia_habil(actual):
                contador += 1
        return actual

    @staticmethod
    def contar_dias_habiles(desde: date, hasta: date) -> int:
        """Cuenta días hábiles entre dos fechas."""
        contador = 0
        actual = desde
        while actual <= hasta:
            if CalculadoraTerminos.es_dia_habil(actual):
                contador += 1
            actual += timedelta(days=1)
        return contador

    async def calcular(
        self,
        tipo: str,
        codigo: str,
        fecha_inicio: date,
        **kwargs,
    ) -> TerminoProcesal:
        """
        Calcula un término procesal.

        Args:
            tipo: Tipo de término (caducidad, prescripcion, traslado, etc.)
            codigo: Código procesal (CGP, CPACA, CPP)
            fecha_inicio: Fecha de inicio del término

        Returns:
            TerminoProcesal con fechas calculadas y alertas
        """
        calculo = self._get_calculo(tipo, codigo)

        if not calculo:
            raise ValueError(
                f"Término '{tipo}' no encontrado para código '{codigo}'. "
                f"Usa listar_terminos() para ver opciones."
            )

        dias_habiles = calculo["dias"]
        norma = calculo["norma"]

        fecha_fin = self.sumar_dias_habiles(fecha_inicio, dias_habiles)
        dias_calendario = (fecha_fin - fecha_inicio).days

        return TerminoProcesal(
            tipo=tipo,
            codigo=codigo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            dias_habiles=dias_habiles,
            dias_calendario=dias_calendario,
            norma=norma,
        )

    def _get_calculo(self, tipo: str, codigo: str) -> Optional[Dict]:
        """Obtiene configuración del cálculo."""
        return self.TERMINOS.get(codigo, {}).get(tipo)

    async def listar_terminos(self, codigo: Optional[str] = None) -> List[Dict]:
        """Lista términos disponibles."""
        if codigo:
            config = self.TERMINOS.get(codigo, {})
            return [
                {"tipo": k, "codigo": codigo, **v}
                for k, v in config.items()
            ]
        return [
            {"tipo": k, "codigo": c, **v}
            for c, config in self.TERMINOS.items()
            for k, v in config.items()
        ]

    # ==========================================
    # Banco de términos procesales colombianos
    # ==========================================

    TERMINOS = {
        "CGP": {
            "traslado_demanda": {
                "dias": 20,
                "norma": "Art. 369 CGP - Traslado de la demanda (proceso verbal)",
            },
            "excepciones_previas": {
                "dias": 10,
                "norma": "Art. 100 CGP - Traslado excepciones previas",
            },
            "recurso_apelacion": {
                "dias": 5,
                "norma": "Art. 322 CGP - Interposición recurso de apelación (verbal)",
            },
            "reposicion": {
                "dias": 3,
                "norma": "Art. 318 CGP - Recurso de reposición",
            },
            "casacion": {
                "dias": 15,
                "norma": "Art. 337 CGP - Recurso de casación",
            },
            "contestar_demanda": {
                "dias": 10,
                "norma": "Art. 369 CGP - Traslado para contestar (verbal sumario)",
            },
            "caducidad_verbal": {
                "dias": 730,  # 2 años
                "norma": "Art. 94 CGP - Caducidad ordinaria (2 años)",
            },
        },
        "CPACA": {
            "caducidad_nulidad": {
                "dias": 120,  # 4 meses
                "norma": "Art. 164.2.d CPACA - Caducidad nulidad y restablecimiento (4 meses)",
            },
            "caducidad_contractual": {
                "dias": 730,  # 2 años
                "norma": "Art. 164.2.e CPACA - Caducidad contractual (2 años)",
            },
            "recurso_reposicion": {
                "dias": 5,
                "norma": "Art. 74 CPACA - Recurso de reposición en vía gubernativa",
            },
            "recurso_apelacion": {
                "dias": 10,
                "norma": "Art. 74 CPACA - Recurso de apelación en vía gubernativa",
            },
            "silencio_administrativo": {
                "dias": 90,  # 3 meses
                "norma": "Art. 83 CPACA - Silencio administrativo negativo (3 meses)",
            },
            "respuesta_peticion": {
                "dias": 15,
                "norma": "Art. 14 CPACA - Término para resolver peticiones (15 días)",
            },
        },
        "CPP": {
            "imputacion": {
                "dias": 730,  # 2 años
                "norma": "Art. 175 CPP - Término para formular imputación (2 años casos complejos)",
            },
            "apelacion_sentencia": {
                "dias": 5,
                "norma": "Art. 179 CPP - Apelación de sentencia penal",
            },
            "detencion_preventiva": {
                "dias": 365,  # 1 año
                "norma": "Art. 317 CPP - Límite de detención preventiva (1 año)",
            },
            "preclusion": {
                "dias": 30,
                "norma": "Art. 333 CPP - Solicitud de preclusión",
            },
        },
    }
