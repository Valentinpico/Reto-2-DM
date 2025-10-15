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
        
        logger.info(f"Conectado a RabbitMQ - Cola: {QUEUE_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error conectando a RabbitMQ: {e}")
        return False


def publish_order_event(order_data: Dict[str, Any]):
    """🔧 Publicar evento con conexión dedicada (Thread-Safe)"""
    
    # Crear conexión dedicada para cada publish (thread-safe)
    try:
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
        
        # Cerrar conexión inmediatamente
        temp_connection.close()
        
        logger.info(f"Mensaje publicado - Order: {order_data.get('order_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error publicando mensaje {order_data.get('order_id')}: {e}")
        return False


def close_rabbitmq_connection():
    """Cerrar conexión a RabbitMQ"""
    global connection
    if connection and not connection.is_closed:
        connection.close()
        logger.info("Conexión a RabbitMQ cerrada")
