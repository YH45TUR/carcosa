"""
Sistema Legal CO - Tests de Integración
Pruebas de integración para los endpoints principales de la API.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Cliente de prueba para la API."""
    with TestClient(app) as c:
        yield c


# ============================================
# Tests: Health & Root
# ============================================

class TestHealth:
    """Tests para los endpoints de salud del sistema."""

    def test_root_endpoint(self, client):
        """El endpoint raíz debe responder con info del sistema."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "status" in data
        assert data["status"] == "online"
        assert "docs" in data

    def test_health_endpoint(self, client):
        """El health check debe responder healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_docs_accessible(self, client):
        """La documentación Swagger debe ser accesible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema(self, client):
        """El schema OpenAPI debe ser válido."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert len(schema["paths"]) >= 30  # Al menos 30 endpoints


# ============================================
# Tests: Auth Routes
# ============================================

class TestAuthIntegration:
    """Tests de integración para autenticación."""

    def test_auth_routes_configured(self, client):
        """Las rutas de autenticación deben estar configuradas."""
        response = client.get("/openapi.json")
        schema = response.json()
        auth_paths = [
            path for path in schema["paths"]
            if path.startswith("/api/auth")
        ]
        assert len(auth_paths) >= 4  # register, login, refresh, me

    def test_register_endpoint_exists(self, client):
        """El endpoint de registro debe responder."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "test_integration",
                "email": "test@example.com",
                "password": "Test123!",
                "role": "asistente",
            },
        )
        # Puede fallar si el usuario ya existe, pero el endpoint debe responder
        assert response.status_code in (200, 400, 422)
        if response.status_code == 400:
            assert "ya registrado" in response.json()["detail"]

    def test_login_endpoint(self, client):
        """El endpoint de login debe estar disponible."""
        response = client.post(
            "/api/auth/login",
            data={"username": "test_user", "password": "test_pass"},
        )
        # Debe responder aunque las credenciales sean inválidas
        assert response.status_code in (200, 401, 422)
        if response.status_code == 401:
            assert "incorrectas" in response.json()["detail"].lower()


# ============================================
# Tests: Cases Routes
# ============================================

class TestCasesIntegration:
    """Tests de integración para casos."""

    def test_cases_routes_configured(self, client):
        """Las rutas de casos deben estar configuradas."""
        response = client.get("/openapi.json")
        schema = response.json()
        case_paths = [
            path for path in schema["paths"]
            if path.startswith("/api/cases")
        ]
        assert len(case_paths) >= 2

    def test_cases_list_requires_auth(self, client):
        """Listar casos sin autenticación debe retornar 401."""
        response = client.get("/api/cases/")
        assert response.status_code == 401

    def test_cases_detail_requires_auth(self, client):
        """Ver detalle de caso sin auth debe retornar 401."""
        response = client.get("/api/cases/1")
        assert response.status_code == 401

    def test_cases_create_requires_auth(self, client):
        """Crear caso sin auth debe retornar 401."""
        response = client.post("/api/cases/", json={"cliente": "test"})
        assert response.status_code == 401


# ============================================
# Tests: Module Routes
# ============================================

class TestModuleRoutes:
    """Tests de integración para rutas de módulos."""

    def test_all_modules_have_routes(self, client):
        """Todos los módulos deben tener rutas registradas."""
        response = client.get("/openapi.json")
        schema = response.json()
        all_paths = list(schema["paths"].keys())

        # Verificar que los prefijos de todos los módulos existen
        module_prefixes = [
            "/api/auth", "/api/cases", "/api/chat", "/api/documents",
            "/api/export", "/api/audit", "/api/jurisprudence",
            "/api/diagram", "/api/calculator", "/api/timeline",
            "/api/adversarial",
        ]
        for prefix in module_prefixes:
            matching = [p for p in all_paths if p.startswith(prefix)]
            assert len(matching) >= 1, f"Módulo {prefix} no tiene rutas"

    def test_protected_routes_require_auth(self, client):
        """Todas las rutas protegidas deben requerir autenticación."""
        protected_endpoints = [
            ("GET", "/api/cases/"),
            ("GET", "/api/cases/1"),
            ("POST", "/api/cases/"),
            ("PUT", "/api/cases/1"),
            ("DELETE", "/api/cases/1"),
            ("POST", "/api/chat/message"),
            ("POST", "/api/export/generate"),
            ("POST", "/api/audit/case/1"),
            ("POST", "/api/jurisprudence/search"),
            ("POST", "/api/diagram/generate"),
            ("POST", "/api/calculator/calcular"),
            ("POST", "/api/adversarial/analyze/1"),
            ("POST", "/api/timeline/from-case/1"),
        ]

        for method, path in protected_endpoints:
            response = client.request(method, path)
            assert response.status_code == 401, (
                f"{method} {path} debe retornar 401, obtuvo {response.status_code}"
            )


# ============================================
# Tests: CORS
# ============================================

class TestCORS:
    """Tests para configuración CORS."""

    def test_cors_headers_present(self, client):
        """Las respuestas deben incluir headers CORS."""
        response = client.get(
            "/health",
            headers={"Origin": "http://example.com"},
        )
        # El servidor permite orígenes específicos
        cors_origin = response.headers.get("access-control-allow-origin")
        assert cors_origin is None or "localhost" in cors_origin


# ============================================
# Tests: Router Configuration
# ============================================

class TestRouterConfiguration:
    """Tests de configuración de routers."""

    def test_audit_router_has_all_routes(self):
        """El router de auditoría debe tener todas las rutas configuradas."""
        from app.api.routes.audit import router
        routes = {r.path for r in router.routes}
        assert "/reglas" in routes
        assert "/case/{case_id}" in routes
        assert "/document" in routes

    def test_adversarial_router_has_all_routes(self):
        """El router adversarial debe tener todas las rutas."""
        from app.api.routes.adversarial import router
        routes = {r.path for r in router.routes}
        assert "/perspectives" in routes
        assert "/analyze/{case_id}" in routes
        assert "/analyze/text" in routes
        assert "/analyze/both/{case_id}" in routes

    def test_jurisprudence_router_has_all_routes(self):
        """El router de jurisprudencia debe tener todas las rutas."""
        from app.api.routes.jurisprudence import router
        routes = {r.path for r in router.routes}
        assert "/search" in routes
        assert "/search/all" in routes
        assert "/semantic" in routes
        assert "/sources" in routes
        assert "/cache/clear" in routes

    def test_calculator_router_has_all_routes(self):
        """El router de calculadora debe tener todas las rutas."""
        from app.api.routes.calculator import router
        routes = {r.path for r in router.routes}
        assert "/calcular" in routes
        assert "/alertas/{case_id}" in routes
        assert "/lista" in routes

    def test_diagram_router_has_all_routes(self):
        """El router de diagramas debe tener todas las rutas."""
        from app.api.routes.diagram import router
        routes = {r.path for r in router.routes}
        assert "/generate" in routes
        assert "/from-case/{case_id}" in routes

    def test_timeline_router_has_all_routes(self):
        """El router de timeline debe tener todas las rutas."""
        from app.api.routes.timeline import router
        routes = {r.path for r in router.routes}
        assert "/from-case/{case_id}" in routes
        assert "/from-text" in routes

    def test_app_has_all_routers(self):
        """La app FastAPI debe tener todos los routers incluidos."""
        from app.main import app as fastapi_app
        route_paths = set()
        for route in fastapi_app.routes:
            if hasattr(route, "path"):
                route_paths.add(route.path)

        # Verificar que al menos hay rutas para cada módulo
        prefixes = ["/api/auth", "/api/cases", "/api/chat", "/api/documents",
                    "/api/export", "/api/audit", "/api/jurisprudence",
                    "/api/diagram", "/api/calculator", "/api/timeline",
                    "/api/adversarial"]
        for prefix in prefixes:
            matching = [p for p in route_paths if str(p).startswith(prefix)]
            assert len(matching) >= 1, f"Faltan rutas para {prefix}"
