"""
Tests for CORS production LAN IP coverage
TDD: fix/cors-production-localhost
"""

from app.core.config import Settings


class TestCorsProductionOrigins:
    """Regression guard for production CORS origins"""

    def test_cors_origins_includes_production_lan_ip(self):
        """Default allowed_origins must include the production LAN IP"""
        settings = Settings()
        origins = settings.get_cors_origins()
        assert "http://192.168.1.237:3000" in origins

    def test_cors_origins_still_includes_localhost(self):
        """Default allowed_origins must still include localhost (regression guard)"""
        settings = Settings()
        origins = settings.get_cors_origins()
        assert "http://localhost:3000" in origins
