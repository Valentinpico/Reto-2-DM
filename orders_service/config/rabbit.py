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
    """Publicar evento de orden creada a RabbitMQ"""
    global channel
    
    try:
        message = json.dumps(order_data)

        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        logger.info(f"📤 Mensaje publicado a cola '{QUEUE_NAME}': {order_data.get('order_id')}")
        return True
    except Exception as e:
        logger.error(f"Error publicando mensaje: {e}")
        if connect_to_rabbitmq():
            try:
                message = json.dumps(order_data)
                channel.basic_publish(
                    exchange='',
                    routing_key=QUEUE_NAME,
                    body=message,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                logger.info(f"📤 Mensaje publicado después de reconexión: {order_data.get('order_id')}")
                return True
            except Exception as retry_error:
                logger.error(f"Error en reintento de publicación: {retry_error}")
                return False
        return False


def close_rabbitmq_connection():
    """Cerrar conexión a RabbitMQ"""
    global connection
    if connection and not connection.is_closed:
        connection.close()
        logger.info("Conexión a RabbitMQ cerrada")
