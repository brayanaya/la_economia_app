"""
Registry de proveedores de catálogo - Selección dinámica basada en configuración y estado.

Este módulo implementa:
- Selección explícita del proveedor mediante configuración
- Control de estado del catálogo (conectado/desconectado/error)
- Validación de que MockProvider NUNCA se use en producción
- Fallback controlado y transparente
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
import logging

from app.core.config import settings
from app.core.catalog_state import catalogo_state, CatalogoEstado
from app.services.providers.base import (
    ProductProvider,
    ProveedorNoDisponibleError,
    ProveedorTimeoutError,
)
from app.services.providers.mock_provider import mock_provider
from app.services.providers.mascontrol_provider import mascontrol_provider

logger = logging.getLogger(__name__)


class ProveedorCatalogo(str, Enum):
    """Proveedores de catálogo disponibles."""
    MOCK = "mock"
    MASCONTROL = "mascontrol"
    AUTO = "auto"  # Selección automática basada en configuración


class ProveedorRegistry:
    """
    Registry centralizado para gestión de proveedores de catálogo.

    Responsabilidades:
    - Seleccionar proveedor según configuración y estado
    - Validar que MockProvider no se use en producción
    - Proporcionar información de estado para frontend/monitoring
    - Manejar errores de proveedores de forma controlada
    """

    def __init__(self):
        self._proveedor_actual: Optional[ProductProvider] = None
        self._proveedor_seleccionado: ProveedorCatalogo = ProveedorCatalogo.AUTO
        self._forzar_mock: bool = False  # Solo para tests explícitos

    def _determinar_proveedor(self) -> ProveedorCatalogo:
        """Determina qué proveedor usar basado en configuración."""
        # Si se forzó mock (tests), usar mock
        if self._forzar_mock:
            return ProveedorCatalogo.MOCK

        # Leer configuración explícita
        proveedor_config = getattr(settings, "catalogo_provider", "auto").lower()

        if proveedor_config in ("mock", "mascontrol", "auto"):
            return ProveedorCatalogo(proveedor_config)

        # Fallback seguro
        logger.warning(f"Proveedor desconocido en config: {proveedor_config}, usando auto")
        return ProveedorCatalogo.AUTO

    def _seleccionar_por_estado(self, proveedor_solicitado: ProveedorCatalogo) -> ProductProvider:
        """
        Selecciona el proveedor real basado en el solicitado y el estado del catálogo.

        REGLAS CRÍTICAS:
        1. MOCK solo en desarrollo/testing explícito
        2. MASCONTROL solo si está configurado Y conectado
        3. AUTO: usa catálogo conectado si está disponible, si no mock (solo dev)
        4. NUNCA fallback silencioso a mock en producción
        """
        estado = catalogo_state.estado
        es_produccion = not settings.debug

        if proveedor_solicitado == ProveedorCatalogo.MOCK:
            if es_produccion:
                raise ProveedorNoDisponibleError(
                    "mock",
                    "PROHIBIDO: MockProvider no puede usarse en producción. "
                    "Configure CATALOG_CONNECTED=true y proveedor MasControl real."
                )
            logger.warning("⚠️  Usando MockProvider (solo desarrollo/testing)")
            return mock_provider

        if proveedor_solicitado == ProveedorCatalogo.MASCONTROL:
            if not mascontrol_provider.esta_disponible:
                raise ProveedorNoDisponibleError(
                    "mascontrol",
                    f"MasControl no configurado: {mascontrol_provider._ultimo_error}. "
                    "Configure variables MASCONTROL_* y reinicie."
                )
            if estado != CatalogoEstado.CONECTADO:
                raise ProveedorNoDisponibleError(
                    "mascontrol",
                    f"Catálogo no conectado (estado: {estado.value}). "
                    "Verifique conexión MasControl antes de seleccionar este proveedor."
                )
            logger.info("✅ Usando MasControlProvider (catálogo real)")
            return mascontrol_provider

        # AUTO - selección inteligente basada en estado real
        if estado == CatalogoEstado.CONECTADO:
            if mascontrol_provider.esta_disponible:
                logger.info("✅ AUTO: Catálogo conectado, usando MasControlProvider")
                return mascontrol_provider
            # CONECTADO pero MasControl no disponible - ERROR en producción y desarrollo
            # El fallback a Mock SOLO debe ocurrir vía inyección de dependencias explícita en tests
            raise ProveedorNoDisponibleError(
                "auto",
                "Catálogo CONECTADO pero MasControl no disponible. Configure MasControl o use forzar_mock_para_tests() en tests."
            )

        if estado == CatalogoEstado.DESCONECTADO:
            if es_produccion:
                raise ProveedorNoDisponibleError(
                    "auto",
                    "Catálogo DESCONECTADO en producción. "
                    "Configure MasControl (CATALOG_CONNECTED=true) o contacte al administrador."
                )
            logger.warning("⚠️  AUTO: Catálogo desconectado, usando MockProvider (SOLO DESARROLLO)")
            return mock_provider

        if estado == CatalogoEstado.DEGRADADO:
            if mascontrol_provider.esta_disponible:
                logger.warning("⚠️  AUTO: Catálogo degradado, intentando MasControlProvider")
                return mascontrol_provider
            if not es_produccion:
                logger.warning("⚠️  AUTO: Catálogo degradado, fallback a MockProvider (SOLO DESARROLLO)")
                return mock_provider
            raise ProveedorNoDisponibleError(
                "auto",
                f"Catálogo DEGRADADO en producción: {catalogo_state.ultimo_error}. "
                "No hay proveedor de respaldo disponible en producción."
            )

        # Estado desconocido - seguro
        raise ProveedorNoDisponibleError(
            "auto",
            f"Estado de catálogo inválido: {estado.value}"
        )

    def obtener_proveedor(self) -> ProductProvider:
        """
        Obtiene el proveedor actual, inicializando si es necesario.

        Returns:
            Instancia del proveedor activo (MockProvider o MasControlProvider)

        Raises:
            ProveedorNoDisponibleError: Si no hay proveedor disponible según reglas
        """
        if self._proveedor_actual is not None:
            return self._proveedor_actual

        proveedor_solicitado = self._determinar_proveedor()
        self._proveedor_seleccionado = proveedor_solicitado
        self._proveedor_actual = self._seleccionar_por_estado(proveedor_solicitado)

        logger.info(f"Proveedor de catálogo inicializado: {self._proveedor_actual.nombre}")
        return self._proveedor_actual

    def forzar_mock_para_tests(self):
        """Fuerza el uso de MockProvider (SOLO para tests automatizados)."""
        if not settings.debug:
            raise RuntimeError("forzar_mock_para_tests() solo permitido en DEBUG=True")
        self._forzar_mock = True
        self._proveedor_actual = None  # Reset para reinicializar
        logger.warning("🧪 TEST MODE: MockProvider forzado")

    def reinicializar(self):
        """Fuerza reinicialización del proveedor (útil tras cambio de config/estado)."""
        self._proveedor_actual = None
        self._forzar_mock = False

    def obtener_info_estado(self) -> dict:
        """Retorna información completa de estado para frontend/monitoring."""
        proveedor = None
        proveedor_nombre = "no_inicializado"
        proveedor_disponible = False
        proveedor_error = None

        try:
            proveedor = self.obtener_proveedor()
            proveedor_nombre = proveedor.nombre
            proveedor_disponible = proveedor.esta_disponible
            # Si el proveedor existe pero no está disponible, capturar su error
            if not proveedor_disponible and hasattr(proveedor, '_ultimo_error') and proveedor._ultimo_error:
                proveedor_error = proveedor._ultimo_error
        except ProveedorNoDisponibleError as e:
            proveedor_error = str(e)
            proveedor_disponible = False
        except Exception as e:
            proveedor_error = f"Error inesperado: {str(e)}"
            proveedor_disponible = False

        estado_catalogo = catalogo_state.obtener_estado_para_frontend()

        # Handle both enum and string for _proveedor_seleccionado
        solicitado = self._proveedor_seleccionado.value if hasattr(self._proveedor_seleccionado, 'value') else str(self._proveedor_seleccionado)

        return {
            "catalogo": estado_catalogo,
            "proveedor": {
                "solicitado": solicitado,
                "activo": proveedor_nombre,
                "disponible": proveedor_disponible,
                "error": proveedor_error,
            },
            "configuracion": {
                "catalog_connected": getattr(settings, "catalog_connected", False),
                "catalogo_provider": getattr(settings, "catalogo_provider", "auto"),
                "debug_mode": settings.debug,
            },
            "reglas": {
                "mock_permitido": settings.debug,
                "mascontrol_requerido_en_produccion": not settings.debug,
                "fallback_automatico_mock": settings.debug and catalogo_state.esta_en_modo_mock,
            }
        }

    async def health_check_completo(self) -> dict:
        """Health check de todo el sistema de catálogo."""
        info = self.obtener_info_estado()

        # Health check del proveedor activo si existe
        if info["proveedor"]["activo"] != "no_inicializado":
            try:
                proveedor = self.obtener_proveedor()
                provider_health = await proveedor.health_check()
                info["proveedor"]["health_check"] = provider_health
            except Exception as e:
                info["proveedor"]["health_check"] = {
                    "estado": "error",
                    "error": str(e),
                }

        return info


# Instancia singleton global
proveedor_registry = ProveedorRegistry()


def get_proveedor_catalogo() -> ProductProvider:
    """
    Dependency injection para FastAPI.
    Retorna el proveedor de catálogo activo según configuración y estado.
    """
    return proveedor_registry.obtener_proveedor()


def get_proveedor_registry() -> ProveedorRegistry:
    """Dependency injection para acceso al registry completo."""
    return proveedor_registry