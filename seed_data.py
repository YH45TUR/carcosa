"""
Sistema Legal CO — Seed Data Script
Puebla la base de datos con datos de demostración para desarrollo y pruebas.

Uso:
    python seed_data.py          # Poblar DB con datos demo
    python seed_data.py --clear  # Limpiar y poblar desde cero
"""
import sys
import os
import argparse
from datetime import date, timedelta, datetime
from passlib.context import CryptContext

# Asegurar que podemos importar desde backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.db.database import SessionLocal, init_db, engine, Base
from app.models.user import User, RevokedToken
from app.models.case import Case, CaseDocument, CaseTerm, TimelineEvent

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed(clear_first: bool = False):
    if clear_first:
        print("[*] Limpiando base de datos existente...")
        Base.metadata.drop_all(bind=engine)

    print("[*] Inicializando tablas...")
    init_db()

    db = SessionLocal()
    try:
        if db.query(User).first():
            print("[!] La base de datos ya tiene datos. Usa --clear para resetear.")
            return

        # ─── Usuarios ─────────────────────────────────────────────────────────
        admin = User(
            username="admin",
            email="admin@sistemalegal.co",
            hashed_password=pwd_context.hash("admin123"),
            role="admin",
            is_active=True,
        )
        abogado = User(
            username="carlos.martinez",
            email="carlos@sistemalegal.co",
            hashed_password=pwd_context.hash("abogado123"),
            role="abogado",
            is_active=True,
        )
        asistente = User(
            username="laura.garcia",
            email="laura@sistemalegal.co",
            hashed_password=pwd_context.hash("asistente123"),
            role="asistente",
            is_active=True,
        )
        db.add_all([admin, abogado, asistente])
        db.flush()

        # ─── Casos ────────────────────────────────────────────────────────────
        hoy = date.today()
        casos = [
            Case(
                cliente="Juan Pérez López",
                demandado="María García Ruiz",
                area="civil",
                status="activo",
                radicado="11001-31-03-001-2024-00001-00",
                juzgado="Juzgado 1° Civil del Circuito de Bogotá",
                cuantia=200_000_000,
                description="Incumplimiento de contrato de compraventa de inmueble.",
                owner_id=abogado.id,
                created_at=datetime.now() - timedelta(days=45),
            ),
            Case(
                cliente="Ana María Rodríguez",
                demandado="EPS Salud Vida S.A.S.",
                area="constitucional",
                status="activo",
                radicado="11001-31-03-001-2024-00002-00",
                juzgado="Juzgado 3° Civil Municipal de Bogotá",
                description="Acción de tutela por negación de procedimiento médico.",
                owner_id=abogado.id,
                created_at=datetime.now() - timedelta(days=30),
            ),
            Case(
                cliente="Pedro Sánchez Hernández",
                demandado="Inversiones del Valle Ltda.",
                area="laboral",
                status="activo",
                radicado="76001-31-05-001-2024-00001-00",
                juzgado="Juzgado 2° Laboral del Circuito de Cali",
                cuantia=85_000_000,
                description="Despido sin justa causa después de 15 años de servicio.",
                owner_id=abogado.id,
                created_at=datetime.now() - timedelta(days=60),
            ),
            Case(
                cliente="Diana Torres Mejía",
                demandado="Entidad Pública Municipal",
                area="administrativo",
                status="archivado",
                radicado="05001-33-33-001-2023-00001-00",
                juzgado="Juzgado 1° Administrativo de Medellín",
                description="Nulidad de acto administrativo que negó licencia de construcción.",
                owner_id=abogado.id,
                created_at=datetime.now() - timedelta(days=200),
            ),
            Case(
                cliente="Familia Gómez Restrepo",
                demandado="Carlos Andrés Vélez",
                area="familia",
                status="activo",
                radicado="11001-31-03-001-2024-00003-00",
                juzgado="Juzgado 2° de Familia de Bogotá",
                description="Proceso de sucesión intestada.",
                owner_id=abogado.id,
                created_at=datetime.now() - timedelta(days=15),
            ),
        ]
        db.add_all(casos)
        db.flush()

        # ─── Términos Procesales ──────────────────────────────────────────────
        terminos = [
            CaseTerm(
                case_id=casos[0].id,
                tipo="traslado_demanda",
                codigo="CGP",
                fecha_inicio=hoy - timedelta(days=10),
                fecha_fin=hoy + timedelta(days=10),
                dias_habiles=20,
                dias_calendario=30,
                norma="Art. 369 CGP - Traslado de la demanda (proceso verbal)",
            ),
            CaseTerm(
                case_id=casos[0].id,
                tipo="recurso_apelacion",
                codigo="CGP",
                fecha_inicio=hoy - timedelta(days=3),
                fecha_fin=hoy + timedelta(days=2),
                dias_habiles=5,
                dias_calendario=7,
                norma="Art. 322 CGP - Interposición recurso de apelación",
            ),
            CaseTerm(
                case_id=casos[1].id,
                tipo="respuesta_peticion",
                codigo="CPACA",
                fecha_inicio=hoy - timedelta(days=14),
                fecha_fin=hoy + timedelta(days=1),
                dias_habiles=15,
                dias_calendario=21,
                norma="Art. 14 CPACA - Término para resolver peticiones",
            ),
        ]
        db.add_all(terminos)

        # ─── Timeline Events ──────────────────────────────────────────────────
        eventos = [
            TimelineEvent(
                case_id=casos[0].id,
                fecha=hoy - timedelta(days=45),
                titulo="Apertura del caso",
                descripcion="Se radicó la demanda ante el juzgado.",
                tipo="apertura",
            ),
            TimelineEvent(
                case_id=casos[0].id,
                fecha=hoy - timedelta(days=40),
                titulo="Admisión de la demanda",
                descripcion="El juzgado admitió la demanda y ordenó el traslado.",
                tipo="procesal",
            ),
            TimelineEvent(
                case_id=casos[0].id,
                fecha=hoy - timedelta(days=10),
                titulo="Notificación al demandado",
                descripcion="Se notificó personalmente al demandado.",
                tipo="notificacion",
            ),
            TimelineEvent(
                case_id=casos[1].id,
                fecha=hoy - timedelta(days=30),
                titulo="Presentación de tutela",
                descripcion="Se interpuso acción de tutela contra la EPS.",
                tipo="apertura",
            ),
        ]
        db.add_all(eventos)
        db.commit()

        print("[✓] Datos de demostración insertados exitosamente:")
        print(f"    • 3 usuarios (admin/abogado/asistente)")
        print(f"    • 5 casos activos/archivados")
        print(f"    • 3 términos procesales calculados")
        print(f"    • 4 eventos de timeline")
        print()
        print("   Credenciales de prueba:")
        print("     admin / admin123")
        print("     carlos.martinez / abogado123")
        print("     laura.garcia / asistente123")

    except Exception as e:
        db.rollback()
        print(f"[!] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poblar DB con datos demo")
    parser.add_argument("--clear", action="store_true", help="Limpiar datos existentes primero")
    args = parser.parse_args()
    seed(clear_first=args.clear)
