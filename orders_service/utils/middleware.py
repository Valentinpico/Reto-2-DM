from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from utils.response import error_response

logger = logging.getLogger(__name__)


async def exception_handler_middleware(request: Request, exc: Exception) -> JSONResponse:
    """
    Middleware para manejar excepciones y estandarizar respuestas de error
    """
    
    # Excepción HTTP personalizada (nuestras excepciones)
    if isinstance(exc, StarletteHTTPException):
        # Si el detail es un dict, es nuestra excepción personalizada
        if isinstance(exc.detail, dict):
            message = exc.detail.get("message", str(exc.detail))
        else:
            message = str(exc.detail)
        
        logger.error(f"❌ HTTP Exception: {exc.status_code} - {message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=message,
                status_code=exc.status_code
            )
        )
    
    # Errores de validación de Pydantic
    elif isinstance(exc, RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"] if x != "body")
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.error(f"❌ Validation Error: {errors}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Errores de validación",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                data={"errors": errors}
            )
        )
    
    # Error interno no controlado
    else:
        logger.error(f"❌ Unhandled Exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                message="Error interno del servidor",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )


def setup_exception_handlers(app):
    """
    Configurar manejadores de excepciones en la aplicación
    """
    app.add_exception_handler(StarletteHTTPException, exception_handler_middleware)
    app.add_exception_handler(RequestValidationError, exception_handler_middleware)
    app.add_exception_handler(Exception, exception_handler_middleware)
