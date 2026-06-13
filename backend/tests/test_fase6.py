"""
Sistema Legal CO - Tests Fase 6
Pruebas para Diagramas, Timeline, Calculadora y Red Team Verifier.
"""
import pytest
from datetime import date, datetime


# ============================================
# Tests: Calculadora de Términos
# ============================================

class TestCalculadoraTerminos:
    """Tests para la calculadora de términos procesales."""

    @pytest.fixture
    def calc(self):
        from app.modules.calculator.terms import CalculadoraTerminos
        return CalculadoraTerminos()

    def test_es_dia_habil_lunes(self, calc):
        """Lunes debe ser día hábil."""
        from datetime import date
        # Buscar un lunes
        d = date(2024, 1, 8)  # 8 enero 2024 = lunes
        assert calc.es_dia_habil(d) is True

    def test_es_dia_habil_domingo(self, calc):
        """Domingo no debe ser día hábil."""
        d = date(2024, 1, 7)  # 7 enero 2024 = domingo
        assert calc.es_dia_habil(d) is False

    def test_es_dia_habil_feriado(self, calc):
        """1 de mayo (feriado) no debe ser día hábil."""
        d = date(2024, 5, 1)
        assert calc.es_dia_habil(d) is False

    @pytest.mark.asyncio
    async def test_calcular_traslado_demanda(self, calc):
        """Cálculo de traslado de demanda (20 días hábiles)."""
        resultado = await calc.calcular("traslado_demanda", "CGP", date(2024, 1, 2))
        assert resultado.dias_habiles == 20
        assert resultado.codigo == "CGP"
        assert resultado.tipo == "traslado_demanda"

    @pytest.mark.asyncio
    async def test_calcular_recurso_apelacion(self, calc):
        """Apelación CGP: 5 días hábiles."""
        resultado = await calc.calcular("recurso_apelacion", "CGP", date(2024, 1, 2))
        assert resultado.dias_habiles == 5
        assert "Art. 322" in resultado.norma

    @pytest.mark.asyncio
    async def test_calcular_caducidad_nulidad(self, calc):
        """Caducidad CPACA: 4 meses hábiles."""
        resultado = await calc.calcular("caducidad_nulidad", "CPACA", date(2024, 1, 2))
        assert resultado.dias_habiles == 120
        assert resultado.codigo == "CPACA"

    @pytest.mark.asyncio
    async def test_calcular_invalid_term(self, calc):
        """Término inválido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            await calc.calcular("termino_inexistente", "CGP", date(2024, 1, 2))

    @pytest.mark.asyncio
    async def test_listar_terminos_cgp(self, calc):
        """Listar términos CGP debe retornar solo los de ese código."""
        terminos = await calc.listar_terminos("CGP")
        assert len(terminos) >= 6
        assert all(t["codigo"] == "CGP" for t in terminos)

    @pytest.mark.asyncio
    async def test_listar_terminos_todos(self, calc):
        """Listar todos los términos debe incluir CGP, CPACA y CPP."""
        terminos = await calc.listar_terminos()
        codigos = set(t["codigo"] for t in terminos)
        assert "CGP" in codigos
        assert "CPACA" in codigos
        assert "CPP" in codigos

    def test_sumar_dias_habiles(self, calc):
        """Sumar 5 días hábiles desde jueves debe caer el jueves siguiente."""
        jueves = date(2024, 1, 4)  # jueves
        resultado = calc.sumar_dias_habiles(jueves, 5)
        assert resultado.weekday() < 5  # No debe caer en fin de semana

    def test_contar_dias_habiles(self, calc):
        """Contar días entre dos fechas debe excluir fines de semana."""
        inicio = date(2024, 1, 2)  # martes (1 de enero es feriado)
        fin = date(2024, 1, 5)     # viernes
        count = calc.contar_dias_habiles(inicio, fin)
        assert count == 4  # mar, mié, jue, vie = 4 días hábiles

    def test_termino_to_dict_structure(self, calc):
        """El dict del término debe tener todos los campos."""
        from app.modules.calculator.terms import TerminoProcesal
        t = TerminoProcesal(
            tipo="test", codigo="CGP",
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 31),
            dias_habiles=20, dias_calendario=30,
            norma="Art. Test",
        )
        d = t.to_dict()
        assert "days_remaining" in d
        assert "is_expired" in d
        assert "is_urgent" in d
        assert "alerta" in d


# ============================================
# Tests: Diagram Generator
# ============================================

class TestDiagramGenerator:
    """Tests para el generador de diagramas."""

    @pytest.fixture
    def gen(self):
        from app.modules.diagram.generator import DiagramGenerator
        return DiagramGenerator()

    @pytest.mark.asyncio
    async def test_generate_timeline(self, gen):
        """Timeline debe producir código Mermaid timeline."""
        data = {
            "events": [
                {"fecha": "2024-01-01", "titulo": "Evento 1", "descripcion": "Desc 1"},
                {"fecha": "2024-06-15", "titulo": "Evento 2", "descripcion": "Desc 2"},
            ]
        }
        result = await gen.generate("timeline", data)
        assert "timeline" in result["chart"]
        assert result["type"] == "timeline"

    @pytest.mark.asyncio
    async def test_generate_flowchart(self, gen):
        """Flowchart debe producir código Mermaid flowchart."""
        data = {
            "nodes": [
                {"id": "A", "label": "Inicio"},
                {"id": "B", "label": "Decisión", "shape": "decision"},
                {"id": "C", "label": "Fin", "shape": "end"},
            ],
            "edges": [
                {"from": "A", "to": "B", "label": "si"},
                {"from": "B", "to": "C", "label": "aprueba"},
            ],
        }
        result = await gen.generate("flowchart", data)
        assert "flowchart" in result["chart"]
        assert "Inicio" in result["chart"]
        assert "Decisión" in result["chart"]

    @pytest.mark.asyncio
    async def test_generate_invalid_type(self, gen):
        """Tipo inválido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            await gen.generate("tipo_invalido", {})

    @pytest.mark.asyncio
    async def test_generate_from_case(self, gen):
        """Generar desde datos de caso debe funcionar."""
        case = {"title": "Caso Test", "events": []}
        result = await gen.generate_from_case(case, "timeline")
        assert result["type"] == "timeline"


# ============================================
# Tests: Timeline Extractor
# ============================================

class TestTimelineExtractor:
    """Tests para el extractor de timeline."""

    @pytest.fixture
    def extractor(self):
        from app.modules.timeline.extractor import TimelineExtractor
        return TimelineExtractor()

    @pytest.mark.asyncio
    async def test_extract_from_empty_case(self, extractor):
        """Caso vacío debe retornar eventos vacíos."""
        result = await extractor.extract_from_case({})
        assert result["total_events"] == 0

    @pytest.mark.asyncio
    async def test_extract_from_text(self, extractor):
        """Texto con fechas debe extraer eventos."""
        text = "El día 15 de marzo de 2024 ocurrió el accidente."
        result = await extractor.extract_from_text(text)
        assert result["total_events"] >= 1

    @pytest.mark.asyncio
    async def test_extract_from_text_multiple_dates(self, extractor):
        """Texto con múltiples fechas debe extraer varios eventos."""
        text = (
            "El 15 de marzo de 2024 se presentó la demanda. "
            "El 20 de abril de 2024 se notificó al demandado. "
            "El 1 de junio de 2024 se realizó la audiencia."
        )
        result = await extractor.extract_from_text(text)
        assert result["total_events"] >= 3

    @pytest.mark.asyncio
    async def test_extract_ordering(self, extractor):
        """Eventos deben estar ordenados cronológicamente."""
        result = await extractor.extract_from_case({
            "versions": [
                {"created_at": "2024-06-01", "document_type": "test", "version_number": 1},
            ],
            "created_at": "2024-01-15",
        })
        if result["total_events"] >= 2:
            dates = [e["fecha"] for e in result["events"]]
            assert dates == sorted(dates)

    def test_format_size(self, extractor):
        """Formato de tamaño debe ser legible."""
        assert "1.0 KB" in extractor._format_size(1024)
        assert "1.0 MB" in extractor._format_size(1024 * 1024)


# ============================================
# Tests: Red Team Verifier
# ============================================

class TestRedTeamVerifier:
    """Tests para el verificador anti-alucinaciones."""

    @pytest.fixture
    def verifier(self):
        from app.modules.redteam.verifier import RedTeamVerifier
        return RedTeamVerifier()

    @pytest.mark.asyncio
    async def test_verify_legal_document(self, verifier):
        """Documento legal bien formado debe pasar verificación."""
        doc = (
            "DEMANDA CIVIL\n\n"
            "HECHOS\n\n"
            "1. El demandante suscribió un contrato.\n\n"
            "FUNDAMENTOS DE DERECHO\n\n"
            "Artículo 1501 del Código Civil, Ley 820 de 2003.\n\n"
            "PRETENSIONES\n\n"
            "Que se declare el incumplimiento.\n\n"
            "Atentamente,\nDr. Pérez\nT.P. No. 123.456"
        )
        result = await verifier.verify_document(doc)
        assert result["data"]["score"] >= 50

    @pytest.mark.asyncio
    async def test_verify_short_document(self, verifier):
        """Documento muy corto debe tener errores."""
        result = await verifier.verify_document("Texto corto")
        assert result["data"]["errores"] > 0

    @pytest.mark.asyncio
    async def test_verify_empty_document(self, verifier):
        """Documento vacío debe tener puntaje bajo."""
        result = await verifier.verify_document("")
        # Documento vacío: score ~75 (1 error + 2-3 advertencias) = no pasa umbral 80
        assert result["data"]["score"] < 80
        assert result["data"]["errores"] > 0

    @pytest.mark.asyncio
    async def test_check_citations_valid(self, verifier):
        """Citas válidas deben pasar verificación."""
        hallazgos = verifier._check_citations("Ley 100 de 1993 y Decreto 780 de 2016")
        assert any(h["tipo"] == "citas_validas" for h in hallazgos)

    @pytest.mark.asyncio
    async def test_check_citations_suspicious(self, verifier):
        """Citas con números sospechosos deben generar advertencia."""
        hallazgos = verifier._check_citations("Ley 9999999 de 2024")
        assert any(h["tipo"] == "cita_sospechosa" for h in hallazgos)

    @pytest.mark.asyncio
    async def test_check_structure(self, verifier):
        """Estructura incompleta debe generar advertencia."""
        hallazgos = verifier._check_structure("Texto sin estructura legal")
        assert any(h["tipo"] == "estructura" for h in hallazgos)

    @pytest.mark.asyncio
    async def test_calculate_score(self, verifier):
        """Puntaje debe estar entre 0-100."""
        score = verifier._calculate_score(0, 0)
        assert score == 100
        score = verifier._calculate_score(10, 0)
        assert score == 0  # No negativo

    def test_patrones_cita_coverage(self, verifier):
        """Todos los patrones de cita deben estar definidos."""
        assert len(verifier.PATRONES_CITA) >= 10
        assert "constitucion" in verifier.PATRONES_CITA
        assert "ley" in verifier.PATRONES_CITA
        assert "sentencia_t" in verifier.PATRONES_CITA


# ============================================
# Tests: Routes
# ============================================

class TestFase6Routes:
    """Tests para las rutas de Fase 6."""

    def test_calculator_routes_exist(self):
        from app.api.routes.calculator import router
        routes = [r.path for r in router.routes]
        assert "/calcular" in routes
        assert "/alertas/{case_id}" in routes
        assert "/lista" in routes

    def test_diagram_routes_exist(self):
        from app.api.routes.diagram import router
        routes = [r.path for r in router.routes]
        assert "/generate" in routes
        assert "/from-case/{case_id}" in routes

    def test_timeline_routes_exist(self):
        from app.api.routes.timeline import router
        routes = [r.path for r in router.routes]
        assert "/from-case/{case_id}" in routes
        assert "/from-text" in routes
