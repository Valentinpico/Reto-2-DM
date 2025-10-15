import os
import json
import pika
import ssl
from dotenv import load_dotenv
import logging
from typing import Dict, Any

load_dotenv()

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "orders_queue"

connection = None
channel = None


def connect_to_rabbitmq():
    """Conectar a RabbitMQ y declarar la cola con soporte SSL para CloudAMQP"""
    global connection, channel
    try:
        parameters = pika.URLParameters(RABBITMQ_URL)
        
        # Configuración para CloudAMQP
        parameters.heartbeat = 30
        parameters.blocked_connection_timeout = 300
        
        # Si la URL usa amqps://, configurar SSL
        if RABBITMQ_URL.startswith('amqps://'):
            context = ssl.create_default_context()
            parameters.ssl_options = pika.SSLOptions(context)
            logger.info("🔒 Usando conexión SSL (amqps)")
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declarar la cola (idempotente)
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        logger.info(f"✅ Conectado a RabbitMQ exitosamente")
        logger.info(f"📦 Cola '{QUEUE_NAME}' declarada")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a RabbitMQ: {e}")
        logger.error(f"📍 URL: {RABBITMQ_URL[:20]}...")  # Solo mostrar inicio por seguridad
        return False


def publish_order_event(order_data: Dict[str, Any]):
    """🔧 Publicar evento con conexión dedicada (Thread-Safe)"""
    
    # ✨ CREAR CONEXIÓN DEDICADA PARA CADA PUBLISH
    try:
        logger.info(f"📡 [PUBLISH] Iniciando publicación para order: {order_data.get('order_id')}")
        
        # Crear conexión específica para este mensaje
        parameters = pika.URLParameters(RABBITMQ_URL)
        
        # Configuración optimizada para Railway
        if "railway.internal" in RABBITMQ_URL or "rlwy.net" in RABBITMQ_URL:
            parameters.heartbeat = 30
            parameters.blocked_connection_timeout = 120
            parameters.socket_timeout = 15
        else:
            parameters.heartbeat = 60
            parameters.blocked_connection_timeout = 300
            
        # SSL si es necesario
        if RABBITMQ_URL.startswith('amqps://'):
            context = ssl.create_default_context()
            parameters.ssl_options = pika.SSLOptions(context)
        
        # Crear conexión temporal
        temp_connection = pika.BlockingConnection(parameters)
        temp_channel = temp_connection.channel()
        
        # Asegurar que la cola existe
        temp_channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Publicar mensaje
        message = json.dumps(order_data)
        temp_channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistente
                content_type='application/json'
            )
        )
        
        # ✨ CERRAR CONEXIÓN INMEDIATAMENTE
        temp_connection.close()
        
        logger.info(f"✅ [PUBLISH SUCCESS] Mensaje publicado exitosamente: {order_data.get('order_id')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ [PUBLISH ERROR] Error publicando mensaje: {e}")
        logger.error(f"📍 Order ID: {order_data.get('order_id')}")
        return False


def close_rabbitmq_connection():
    """Cerrar conexión a RabbitMQ"""
    global connection
    if connection and not connection.is_closed:
        connection.close()
        logger.info("Conexión a RabbitMQ cerrada")
