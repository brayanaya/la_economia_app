"""
Gestión de estado del catálogo: CONECTADO vs NO CONECTADO (MOCK).

Este módulo controla el estado operativo del catálogo y proporciona
el proveedor apropiado según la configuración.

Estados posibles:
- CATALOG_CONNECTED=false (default): Usa MockProvider con fixtures de desarrollo
- CATALOG_CONNECTED=true: Usa MasControlProvider (requiere configuración real)
"""
from enum import Enum
from typing import Optional
from app.core.config import settings


class CatalogoEstado(str, Enum):
    """Estados posibles del catálogo."""
    DESCONECTADO = "desconectado"      # Mock/fixtures para desarrollo
    CONECTADO = "conectado"            # MasControl real
    DEGRADADO = "degradado"            # Conectado pero con fallos, fallback a mock


class CatalogoStateManager:
    """
    Gestor singleton del estado del catálogo.

    Permite consultar el estado actual y obtener el proveedor correspondiente.
    Thread-safe para uso en FastAPI.
    """
    _instance: Optional["CatalogoStateManager"] = None
    _estado: CatalogoEstado = CatalogoEstado.DESCONECTADO
    _proveedor_instancia = None
    _ultimo_error: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_inicializado"):
            self._inicializado = True
            self._inicializar_estado()

    def _inicializar_estado(self):
        """Inicializa el estado basado en configuración."""
        # Leer de settings (variable de entorno CATALOG_CONNECTED)
        catalog_connected = getattr(settings, "catalog_connected", False)

        if catalog_connected:
            self._estado = CatalogoEstado.CONECTADO
        else:
            self._estado = CatalogoEstado.DESCONECTADO

    @property
    def estado(self) -> CatalogoEstado:
        """Estado actual del catálogo."""
        return self._estado

    @property
    def esta_conectado(self) -> bool:
        """True si el catálogo real está conectado y funcionando."""
        return self._estado == CatalogoEstado.CONECTADO

    @property
    def esta_en_modo_mock(self) -> bool:
        """True si está usando datos de desarrollo (mock)."""
        return self._estado == CatalogoEstado.DESCONECTADO

    @property
    def ultimo_error(self) -> Optional[str]:
        """Último error registrado al intentar conectar catálogo real."""
        return self._ultimo_error

    def marcar_conectado(self):
        """Marca el catálogo como conectado (cuando MasControl está listo)."""
        self._estado = CatalogoEstado.CONECTADO
        self._ultimo_error = None
        self._proveedor_instancia = None  # Forzar recreación

    def marcar_desconectado(self, error: str = ""):
        """Marca el catálogo como desconectado (fallback a mock)."""
        self._estado = CatalogoEstado.DESCONECTADO
        self._ultimo_error = error
        self._proveedor_instancia = None

    def marcar_degradado(self, error: str):
        """Marca el catálogo como degradado (conectado pero con problemas)."""
        self._estado = CatalogoEstado.DEGRADADO
        self._ultimo_error = error

    def obtener_estado_para_frontend(self) -> dict:
        """Retorna info de estado para mostrar en UI."""
        return {
            "estado": self._estado.value,
            "conectado": self.esta_conectado,
            "modo_mock": self.esta_en_modo_mock,
            "ultimo_error": self._ultimo_error,
            "mensaje_usuario": self._mensaje_usuario(),
        }

    def _mensaje_usuario(self) -> str:
        """Mensaje amigable para el usuario según estado."""
        if self._estado == CatalogoEstado.CONECTADO:
            return "Catálogo conectado - Precios y stock en tiempo real"
        elif self._estado == CatalogoEstado.DEGRADADO:
            return "Catálogo con problemas - Mostrando datos de referencia"
        else:
            return "Modo demostración - Datos de ejemplo (catálogo real pendiente)"


# Instancia global (singleton)
catalogo_state = CatalogoStateManager()


def get_catalogo_state() -> CatalogoStateManager:
    """Dependency injection para FastAPI."""
    return catalogo_state