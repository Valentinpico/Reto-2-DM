import os
import json
import pika
import ssl
import time
import logging
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
ORDERS_API_URL = os.getenv("ORDERS_API_URL", "http://orders_service:8000")
QUEUE_NAME = "orders_queue"
MAX_RETRIES = 10
RETRY_DELAY = 5


def connect_to_rabbitmq():
    """Conectar a RabbitMQ con reintentos y soporte SSL para CloudAMQP"""
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            logger.info(f"🔄 Intentando conectar a RabbitMQ... (intento {retries + 1}/{MAX_RETRIES})")
            
            # Parsear URL
            parameters = pika.URLParameters(RABBITMQ_URL)
            
            # Configuración para CloudAMQP
            parameters.heartbeat = 30
            parameters.blocked_connection_timeout = 300
            
            # Si la URL usa amqps://, configurar SSL
            if RABBITMQ_URL.startswith('amqps://'):
                context = ssl.create_default_context()
                # CloudAMQP usa certificados válidos, no necesitamos deshabilitarlos
                parameters.ssl_options = pika.SSLOptions(context)
                logger.info("🔒 Usando conexión SSL (amqps)")
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            
            logger.info(f"✅ Conectado a RabbitMQ exitosamente")
            logger.info(f"👂 Escuchando cola: '{QUEUE_NAME}'")
            
            return connection, channel
            
        except Exception as e:
            retries += 1
            logger.error(f"❌ Error conectando a RabbitMQ: {e}")
            logger.error(f"📍 URL: {RABBITMQ_URL[:20]}...")  # Solo mostrar inicio de URL por seguridad
            
            if retries < MAX_RETRIES:
                logger.info(f"⏳ Reintentando en {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("💀 Se alcanzó el máximo de reintentos")
                raise


def update_order_status(order_id: str, status: str = "notified") -> bool:
    """
    🔔 Llamar a Orders API para actualizar el estado del pedido
    
    Args:
        order_id: ID del pedido a actualizar
        status: Nuevo estado (default: "notified")
        
    Returns:
        bool: True si se actualizó exitosamente, False en caso contrario
    """
    try:
        url = f"{ORDERS_API_URL}/api/orders/{order_id}/status"
        params = {"new_status": status}
        
        logger.info(f"📡 Actualizando estado del pedido {order_id} a '{status}'...")
        
        response = requests.patch(url, params=params, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ API Response: Estado actualizado exitosamente")
            return True
        else:
            logger.error(f"❌ Error en API: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ No se pudo conectar a Orders API en {ORDERS_API_URL}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout conectando a Orders API")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado llamando API: {e}")
        return False


def callback(ch, method, properties, body):
    """
    Callback que se ejecuta cuando se recibe un mensaje de la cola
    """
    try:
        # Decodificar mensaje JSON
        message = json.loads(body.decode('utf-8'))
        
        order_id = message.get("order_id", "unknown")
        customer_id = message.get("customer_id", "unknown")
        total_amount = message.get("total_amount", 0)
        products = message.get("products", [])
        
        # Log del mensaje recibido
        logger.info("=" * 70)
        logger.info("NUEVO PEDIDO RECIBIDO")
        logger.info(f"Order ID:     {order_id}")
        logger.info(f"Customer ID:  {customer_id}")
        

        logger.info(f"Productos:    {len(products)} item(s)")
        for idx, product in enumerate(products, 1):
            logger.info(f"   - {product}")

        logger.info(f"TOTAL:        ${total_amount}")
        logger.info("=" * 70)
        
        # ✨ FUNCIONALIDAD EXTRA: Actualizar estado del pedido
        logger.info("🕐 Esperando 4 segundos antes de confirmar notificación...")
        time.sleep(4)  # Dar tiempo para consultar el estado
        
        # Llamar API para actualizar estado
        success = update_order_status(order_id)
        
        if success:
            logger.info(f"✅ NOTIFICACIÓN CONFIRMADA - Pedido {order_id} actualizado a 'notified'")
        else:
            logger.warning(f"⚠️  Notificación procesada pero no se pudo actualizar estado del pedido {order_id}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("🔄 Mensaje procesado y confirmado (ACK)")
        logger.info("=" * 70)
        logger.info("")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {e}")
        logger.error(f"Mensaje recibido: {body}")

        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    """Iniciar el consumer de RabbitMQ"""
    logger.info("🚀 Notifications Service iniciado")
    logger.info("⏳ Esperando mensajes de pedidos...")
    
    try:
        connection, channel = connect_to_rabbitmq()
        
        # Configurar prefetch para procesar un mensaje a la vez
        channel.basic_qos(prefetch_count=1)
        
        # Comenzar a consumir mensajes
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=callback,
            auto_ack=False  # ACK manual
        )
        
        logger.info("Consumer listo. Presiona CTRL+C para detener.")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Consumer detenido por el usuario")
        if connection and not connection.is_closed:
            connection.close()
        logger.info("Notifications Service finalizado")

    except Exception as e:
        logger.error(f"Error fatal en el consumer: {e}")
        raise


if __name__ == "__main__":
    start_consumer()
