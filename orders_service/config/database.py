import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/ordersdb")

client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Conectar a MongoDB"""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.get_database()
        # Test connection
        await client.admin.command('ping')
        logger.info(f"Conectado a MongoDB: {MONGODB_URL}")
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global client
    if client:
        client.close()
        logger.info("Conexión a MongoDB cerrada")


def get_database():
    """Obtener instancia de la base de datos"""
    return database
