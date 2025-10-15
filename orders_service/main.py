from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from config.database import connect_to_mongo, close_mongo_connection
from config.rabbit import connect_to_rabbitmq, close_rabbitmq_connection
from routes.orders import router as orders_router
from utils.middleware import setup_exception_handlers
from utils.response import success_response
from models.responses import HealthResponseModel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar el ciclo de vida de la aplicación"""
    # Startup
    await connect_to_mongo()
    connect_to_rabbitmq()
    logger.info("🚀 Orders Service iniciado")
    yield
    # Shutdown
    await close_mongo_connection()
    close_rabbitmq_connection()
    logger.info("👋 Orders Service finalizado")


app = FastAPI(
    title="Orders Service API",
    description="Microservicio de pedidos con FastAPI, MongoDB y RabbitMQ",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar manejadores de excepciones
setup_exception_handlers(app)


# Middleware para medir tiempo de respuesta
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware que mide el tiempo de respuesta de cada request
    y lo registra en los logs
    """
    start_time = time.time()
    
    # Log del request
    logger.info(f"📥 {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Agregar header con tiempo de respuesta
        response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
        
        # Log del response
        logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {round(process_time, 2)}ms"
        )
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"❌ {request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {round(process_time, 2)}ms"
        )
        raise


# Incluir routers
app.include_router(orders_router)


# Endpoint de salud
@app.get(
    "/",
    tags=["health"],
    response_model=HealthResponseModel,
    summary="Health Check",
    description="Verifica que el servicio esté funcionando correctamente"
)
async def health_check():
    """
    Health Check del Orders Service
    
    Retorna el estado del servicio para verificar que está operativo.
    """
    return success_response(
        data={
            "status": "healthy",
            "service": "Orders Service",
            "version": "1.0.0"
        },
        message="Orders Service está funcionando correctamente"
    )


@app.get(
    "/health",
    tags=["health"],
    response_model=HealthResponseModel,
    summary="Health Check Detallado",
    description="Verifica el estado del servicio y sus dependencias"
)
async def detailed_health_check():
    """
    Health Check Detallado
    
    Verifica el estado del servicio y sus conexiones:
    - MongoDB
    - RabbitMQ
    """
    from config.database import get_database
    
    health_status = {
        "service": "Orders Service",
        "version": "1.0.0",
        "mongodb": "disconnected",
        "rabbitmq": "disconnected"
    }
    
    # Verificar MongoDB
    try:
        db = get_database()
        if db is not None:
            health_status["mongodb"] = "connected"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
    
    # Verificar RabbitMQ
    from config.rabbit import connection
    if connection and not connection.is_closed:
        health_status["rabbitmq"] = "connected"
    
    return success_response(
        data=health_status,
        message="Health check completado"
    )
