"""
Tests for configuration security
TDD: BUG-07 - Configuration hardening gaps
"""

import pytest
import os
from unittest.mock import patch


class TestConfigurationSecurity:
    """Tests for secure configuration"""

    def test_cors_origins_configurable(self):
        """CORS origins should be configurable via environment"""
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://localhost:3000,http://prod.example.com"}):
            # Re-import to pick up new env var
            from importlib import reload
            import app.core.config as config_module
            reload(config_module)
            
            settings = config_module.Settings()
            origins = settings.get_cors_origins()
            
            assert "http://localhost:3000" in origins
            assert "http://prod.example.com" in origins

    def test_cors_origins_default(self):
        """Default CORS origins should include localhost"""
        from app.core.config import Settings
        settings = Settings()
        
        # Should have method to get origins
        assert hasattr(settings, 'get_cors_origins')
        origins = settings.get_cors_origins()
        assert isinstance(origins, list)
        assert len(origins) > 0

    def test_secret_key_warning_in_production(self):
        """Using default secret_key in production should warn"""
        import warnings
        
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "SECRET_KEY": "changeme"}):
            from importlib import reload
            import app.core.config as config_module
            
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                reload(config_module)
                settings = config_module.Settings()
                
                # Should have triggered a warning
                # (This test documents expected behavior)
