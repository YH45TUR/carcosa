"""
Sistema Legal CO - Tests de Auditoría Legal
Pruebas para los módulos de auditoría, testimonios y adversarial.
"""
import pytest
from datetime import datetime


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def sample_document_text():
    """Texto de ejemplo para auditoría."""
    return """JUZGADO PRIMERO CIVIL DEL CIRCUITO DE BOGOTÁ

Radicado: 11001-31-03-001-2024-00001-00

DEMANDANTE: JUAN PÉREZ LÓPEZ
DEMANDADO: MARÍA GARCÍA RUIZ

HECHOS

Primero: El día 15 de marzo de 2024, las partes suscribieron un contrato de compraventa.

FUNDAMENTOS DE DERECHO

Artículo 1501 del Código Civil, Ley 820 de 2003.

PRETENSIONES

Que se declare civilmente responsable al demandado.

PRUEBAS

Documental: Copia del contrato.
Testimonial: Declaración de testigos.

NOTIFICACIONES

Dirección: Calle 100 No. 15-30
Correo: juan@email.com

Atentamente,

Carlos Martínez
Abogado
T.P. No. 123.456"""


@pytest.fixture
def rules():
    """Referencia a las reglas de auditoría."""
    from app.modules.audit.rules import ReglasAuditoria
    return ReglasAuditoria


@pytest.fixture
def auditor():
    """Instancia del LegalAuditor."""
    from app.modules.audit.auditor import LegalAuditor
    return LegalAuditor()


@pytest.fixture
def testimony_analyzer():
    """Instancia del TestimonyAnalyzer."""
    from app.modules.testimony.analyzer import TestimonyAnalyzer
    return TestimonyAnalyzer()


# ============================================
# Tests: ReglasAuditoria
# ============================================

class TestReglasAuditoria:
    """Tests para el banco de reglas de auditoría."""

    def test_get_all_rules(self, rules):
        """Debe retornar todas las reglas registradas."""
        all_rules = rules.get_all_rules()
        assert len(all_rules) >= 10
        assert len(rules.REGLAS_CGP) >= 3
        assert len(rules.REGLAS_CPACA) >= 2
        assert len(rules.REGLAS_CPP) >= 1
        assert len(rules.REGLAS_GENERALES) >= 3

    def test_get_rules_by_code(self, rules):
        """Debe filtrar reglas por código procesal."""
        cgp_rules = rules.get_rules_by_code("CGP")
        assert len(cgp_rules) >= 3
        assert all("CGP" in r.codigo for r in cgp_rules)

        cpaca_rules = rules.get_rules_by_code("CPACA")
        assert len(cpaca_rules) >= 2
        assert all("CPACA" in r.codigo for r in cpaca_rules)

    def test_get_rules_by_criticidad(self, rules):
        """Debe filtrar reglas por criticidad."""
        from app.modules.audit.rules import Criticidad

        criticas = rules.get_rules_by_criticidad(Criticidad.CRITICO)
        assert len(criticas) >= 3
        assert all(r.criticidad == Criticidad.CRITICO for r in criticas)

        bajas = rules.get_rules_by_criticidad(Criticidad.BAJO)
        assert len(bajas) >= 1

    def test_get_automatizable_rules(self, rules):
        """Debe retornar solo reglas automatizables."""
        auto_rules = rules.get_automatizable_rules()
        assert len(auto_rules) >= 5
        assert all(r.automatizable for r in auto_rules)

    def test_validate_text_with_juramento(self, rules):
        """Texto con juramento no debe generar hallazgo."""
        text = "Bajo el juramento afirmo que los hechos son ciertos."
        hallazgos = rules.validate_text(text)
        codigos = [h.codigo for h in hallazgos]
        assert "CGP-82-10" not in codigos

    def test_validate_text_without_juramento(self, rules):
        """Texto sin juramento debe generar hallazgo."""
        text = "Presento demanda sin ninguna afirmación juramentada."
        hallazgos = rules.validate_text(text)
        codigos = [h.codigo for h in hallazgos]
        assert "CGP-82-10" in codigos

    def test_validate_text_with_tp(self, rules):
        """Texto con T.P. no debe generar hallazgo."""
        text = "Atentamente, Dr. Pérez. T.P. No. 123.456"
        hallazgos = rules.validate_text(text)
        codigos = [h.codigo for h in hallazgos]
        assert "EST-001" not in codigos

    def test_validate_text_without_tp(self, rules):
        """Texto sin T.P. debe generar hallazgo."""
        text = "Atentamente, Dr. Pérez."
        hallazgos = rules.validate_text(text)
        codigos = [h.codigo for h in hallazgos]
        assert "EST-001" in codigos

    def test_validate_text_conciliacion(self, rules):
        """Texto con conciliación no debe generar hallazgo CPACA."""
        text = "Se agotó la conciliación extrajudicial."
        hallazgos = rules.validate_text(text)
        codigos = [h.codigo for h in hallazgos]
        assert "CPACA-161" not in codigos

    @pytest.mark.parametrize("codigo", ["CGP", "CPACA", "CPP"])
    def test_get_rules_by_code_all(self, rules, codigo):
        """Debe retornar reglas para cada código soportado."""
        code_rules = rules.get_rules_by_code(codigo)
        assert len(code_rules) >= 1

    def test_hallazgo_structure(self, rules):
        """Cada hallazgo debe tener todos los campos requeridos."""
        from app.modules.audit.rules import Criticidad

        for rule in rules.get_all_rules():
            assert rule.criticidad in Criticidad
            assert rule.titulo
            assert rule.descripcion
            assert rule.norma
            assert rule.sugerencia
            assert rule.codigo


# ============================================
# Tests: LegalAuditor
# ============================================

class TestLegalAuditor:
    """Tests para el auditor legal."""

    @pytest.mark.asyncio
    async def test_audit_document(self, auditor, sample_document_text):
        """Auditar documento debe retornar resultado estructurado."""
        result = await auditor.audit_document(sample_document_text, "CGP")
        assert result["success"]
        assert "data" in result
        assert result["data"]["total_hallazgos"] >= 0

    @pytest.mark.asyncio
    async def test_audit_case_without_text(self, auditor):
        """Auditar caso sin texto debe funcionar."""
        result = await auditor.audit_case(case_id=1, message="Revisar caso")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_audit_document_empty(self, auditor):
        """Texto vacío debe retornar análisis sin hallazgos."""
        result = await auditor.audit_document("", "CGP")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_audit_multiple_codes(self, auditor, sample_document_text):
        """Auditar con diferentes códigos debe funcionar."""
        for codigo in ["CGP", "CPACA", "CPP"]:
            result = await auditor.audit_document(sample_document_text, codigo)
            assert result["success"]


# ============================================
# Tests: TestimonyAnalyzer
# ============================================

class TestTestimonyAnalyzer:
    """Tests para el analizador de testimonios."""

    @pytest.mark.asyncio
    async def test_analyze_empty_text(self, testimony_analyzer):
        """Texto vacío debe retornar resultado vacío."""
        result = await testimony_analyzer.analyze("")
        assert result["total_declaraciones"] == 0
        assert result["total_contradicciones"] == 0

    @pytest.mark.asyncio
    async def test_analyze_with_declarations(self, testimony_analyzer):
        """Texto con declaraciones debe extraerlas."""
        text = "El testigo manifestó que vio al acusado salir del edificio a las 5 PM."
        result = await testimony_analyzer.analyze(text)
        assert result["total_declaraciones"] >= 1

    @pytest.mark.asyncio
    async def test_analyze_with_contradictions(self, testimony_analyzer):
        """Texto con contradicciones debe detectarlas."""
        text = (
            "El testigo afirmó que estaba en su casa. "
            "Sin embargo, otro testigo dijo que lo vio en el parque "
            "a la misma hora. Por un lado, la primera versión parece "
            "creíble, pero por otro lado hay evidencia en contrario."
        )
        result = await testimony_analyzer.analyze(text)
        assert result["total_contradicciones"] >= 1

    @pytest.mark.asyncio
    async def test_extract_persons(self, testimony_analyzer):
        """Texto con nombres debe extraer personas."""
        text = "El Dr. Juan Pérez declaró. La Sra. María García confirmó."
        result = await testimony_analyzer.analyze(text)
        assert len(result["personas_mencionadas"]) >= 1

    @pytest.mark.asyncio
    async def test_extract_key_facts(self, testimony_analyzer):
        """Texto con fechas debe extraer hechos clave."""
        text = "El 15 de marzo de 2024 ocurrió el accidente."
        result = await testimony_analyzer.analyze(text)
        assert len(result["hechos_clave"]) >= 1

    @pytest.mark.asyncio
    async def test_classify_declaration_juramento(self, testimony_analyzer):
        """Declaración bajo juramento debe clasificarse correctamente."""
        text = "Bajo la gravedad del juramento afirmo que los hechos son ciertos."
        result = await testimony_analyzer.analyze(text)
        assert len(result["declaraciones"]) >= 1


# ============================================
# Tests: Adversarial
# ============================================

class TestAdversarialPrompts:
    """Tests para los prompts adversariales."""

    def test_get_perspective_judge(self):
        """Perspectiva judge debe retornar configuración."""
        from app.modules.adversarial.prompts import get_perspective

        config = get_perspective("judge")
        assert config["name"] == "Ojo del Juez"
        assert "system_prompt" in config
        assert len(config["system_prompt"]) > 100

    def test_get_perspective_opponent(self):
        """Perspectiva opponent debe retornar configuración."""
        from app.modules.adversarial.prompts import get_perspective

        config = get_perspective("opponent")
        assert config["name"] == "Contra-Parte Virtual"
        assert "system_prompt" in config

    def test_get_perspective_invalid(self):
        """Perspectiva inválida debe lanzar ValueError."""
        from app.modules.adversarial.prompts import get_perspective

        with pytest.raises(ValueError):
            get_perspective("invalid_perspective")

    def test_get_available_perspectives(self):
        """Debe listar perspectivas disponibles."""
        from app.modules.adversarial.prompts import get_available_perspectives

        perspectives = get_available_perspectives()
        assert len(perspectives) == 2
        assert "judge" in perspectives
        assert "opponent" in perspectives


class TestAdversarialAnalyzer:
    """Tests para el analizador adversarial."""

    @pytest.mark.asyncio
    async def test_analyze_empty_text(self):
        """Texto vacío debe retornar error controlado."""
        from app.modules.adversarial.analyzer import AdversarialAnalyzer
        analyzer = AdversarialAnalyzer()

        result = await analyzer.analyze("", "judge")
        assert not result["success"]

    @pytest.mark.asyncio
    async def test_analyze_offline_judge(self):
        """Análisis offline judge debe tener estructura esperada."""
        from app.modules.adversarial.analyzer import AdversarialAnalyzer
        analyzer = AdversarialAnalyzer()

        result = analyzer._analyze_offline("Texto de prueba para análisis", "judge")
        assert "analisis_completo" in result
        assert "fortalezas" in result
        assert "debilidades" in result

    @pytest.mark.asyncio
    async def test_analyze_offline_opponent(self):
        """Análisis offline opponent debe tener estructura esperada."""
        from app.modules.adversarial.analyzer import AdversarialAnalyzer
        analyzer = AdversarialAnalyzer()

        result = analyzer._analyze_offline("Texto de prueba para análisis", "opponent")
        assert "analisis_completo" in result
        assert "estrategia_ataque" in result
        assert "puntos_debiles_explotables" in result

    @pytest.mark.asyncio
    async def test_invalid_perspective(self):
        """Perspectiva inválida debe retornar error."""
        from app.modules.adversarial.analyzer import AdversarialAnalyzer
        analyzer = AdversarialAnalyzer()

        result = await analyzer.analyze("Texto de prueba", "invalid")
        assert not result["success"]
        assert "available_perspectives" in result


# ============================================
# Tests: Audit Routes
# ============================================

class TestAuditRoutes:
    """Tests para los endpoints de auditoría."""

    def test_audit_rules_endpoint(self):
        """El endpoint de reglas debe estar configurado."""
        from app.api.routes.audit import router
        routes = [r.path for r in router.routes]
        assert "/reglas" in routes
        assert "/case/{case_id}" in routes
        assert "/document" in routes

    def test_adversarial_routes(self):
        """Los endpoints adversariales deben estar configurados."""
        from app.api.routes.adversarial import router
        routes = [r.path for r in router.routes]
        assert "/perspectives" in routes
        assert "/analyze/{case_id}" in routes
        assert "/analyze/text" in routes
        assert "/analyze/both/{case_id}" in routes

    def test_testimony_analyzer_empty(self):
        """Test rápido del analizador de testimonios."""
        from app.modules.testimony.analyzer import TestimonyAnalyzer
        analyzer = TestimonyAnalyzer()

        # Prueba sincrónica del método de similitud
        sim = analyzer._text_similarity("texto uno", "texto uno")
        assert sim > 0.9

        sim_diff = analyzer._text_similarity("texto completamente diferente", "otro tema distinto")
        assert sim_diff < 0.5
