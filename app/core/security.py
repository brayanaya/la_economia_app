"""
Middlewares de seguridad de la API.

- SecurityHeadersMiddleware: encabezados de endurecimiento basicos.
- RateLimitMiddleware: limite de peticiones por IP, en memoria (ventana
  deslizante). Es por proceso, se reinicia con el servidor y usa la IP del
  socket; detras de un proxy habria que leer X-Forwarded-For desde un proxy
  de confianza o delegar el limite al proxy.
"""
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, reglas: dict[str, tuple[int, int]]) -> None:
        super().__init__(app)
        # reglas: sufijo de ruta -> (maximo de peticiones, ventana en segundos)
        self._reglas = reglas
        self._aciertos: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            for sufijo, (maximo, ventana) in self._reglas.items():
                if request.url.path.endswith(sufijo):
                    ip = request.client.host if request.client else "desconocida"
                    ahora = time.monotonic()
                    registro = self._aciertos[(ip, sufijo)]
                    while registro and ahora - registro[0] > ventana:
                        registro.popleft()
                    if len(registro) >= maximo:
                        espera = max(1, int(ventana - (ahora - registro[0])) + 1)
                        return JSONResponse(
                            {"detail": "Demasiadas peticiones. Intenta de nuevo en unos segundos."},
                            status_code=429,
                            headers={"Retry-After": str(espera)},
                        )
                    registro.append(ahora)
                    break
        return await call_next(request)