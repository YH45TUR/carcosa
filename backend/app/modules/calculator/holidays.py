"""
Festivos colombianos y recesos judiciales.

Fuentes:
  - Festivos: Ley 51/1983 (festivos nacionales) con dias puente (Ley Emiliani)
  - Recesos: Acuerdo PCSJA del CSJ (actualizar anualmente con el nuevo acuerdo)

USO:
  from app.modules.calculator.holidays import add_business_days, is_business_day

  due = add_business_days(date.today(), 20)  # 20 dias habiles desde hoy
"""
from __future__ import annotations

from datetime import date, timedelta
import holidays


def get_colombia_holidays(year: int) -> set[date]:
    """
    Retorna todos los festivos nacionales colombianos para el ano dado.
    Usa la libreria `holidays` con pais CO + dias puente (Ley Emiliani).
    """
    co_holidays = holidays.Colombia(years=year)
    return set(co_holidays.keys())


# ─── Recesos judiciales ─────────────────────────────────────────────────────────
# En estas fechas los terminos se SUSPENDEN (diferente a dia no habil).
# IMPORTANTE: actualizar cada ano con el Acuerdo PCSJA del CSJ.

JUDICIAL_RECESSES: list[tuple[date, date]] = [
    # (inicio_inclusive, fin_inclusive)
    (date(2025, 12, 20), date(2026, 1, 12)),   # receso dic-ene 2025-2026
    (date(2026, 4, 2),   date(2026, 4, 5)),    # Semana Santa 2026
    (date(2026, 6, 29),  date(2026, 7, 3)),    # receso mitad de ano 2026
    (date(2026, 12, 19), date(2027, 1, 11)),   # receso dic-ene 2026-2027
]


def is_judicial_recess(d: date) -> bool:
    """Retorna True si la fecha cae en receso judicial."""
    for start, end in JUDICIAL_RECESSES:
        if start <= d <= end:
            return True
    return False


def is_business_day(d: date, include_saturdays: bool = False) -> bool:
    """
    Determina si una fecha es dia habil judicial.
    Los sabados NO son habiles bajo CGP, CPACA ni CPP por defecto.
    Los dias dentro de receso judicial tampoco son habiles.
    """
    if d.weekday() == 6:  # domingo
        return False
    if not include_saturdays and d.weekday() == 5:  # sabado
        return False
    if d in get_colombia_holidays(d.year):
        return False
    if is_judicial_recess(d):
        return False
    return True


def add_business_days(
    start: date,
    n_days: int,
    include_saturdays: bool = False,
    suspend_during_recess: bool = True,
) -> date:
    """
    Suma n_days dias habiles judiciales a start (start NO cuenta).
    Si suspend_during_recess=True, los dias dentro de receso no se cuentan
    (comportamiento correcto segun CGP Art. 117).
    """
    current = start
    counted = 0
    while counted < n_days:
        current += timedelta(days=1)
        if is_business_day(current, include_saturdays):
            if not (suspend_during_recess and is_judicial_recess(current)):
                counted += 1
    return current


def count_business_days_between(start: date, end: date, include_saturdays: bool = False) -> int:
    """Cuenta dias habiles judiciales entre dos fechas (ambas exclusivas)."""
    count = 0
    current = start + timedelta(days=1)
    while current < end:
        if is_business_day(current, include_saturdays):
            count += 1
        current += timedelta(days=1)
    return count
