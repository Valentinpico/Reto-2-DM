import os
import json
import pika
import pika.exceptions
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

# ✨ CONTADORES PARA DEBUGGING
message_counter = 0
last_message_time = None


def connect_to_rabbitmq():
    """🚀 Conectar a RabbitMQ con configuración específica para Railway"""
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            logger.info(f"🔄 Intentando conectar a RabbitMQ... (intento {retries + 1}/{MAX_RETRIES})")
            
            # ✨ CONFIGURACIÓN ESPECÍFICA PARA RAILWAY PROXY
            is_railway = "railway.internal" in RABBITMQ_URL or "rlwy.net" in RABBITMQ_URL
            
            if is_railway:
                logger.info("🚂 Detectado Railway - usando configuración optimizada")
                # Configuración especial para Railway
                parameters = pika.URLParameters(RABBITMQ_URL)
                parameters.heartbeat = 30  # Más conservador para proxy
                parameters.blocked_connection_timeout = 120  # 2 minutos
                parameters.connection_attempts = 5
                parameters.retry_delay = 2
                parameters.socket_timeout = 15
                # Configuración TCP específica para Railway
                parameters.tcp_options = {
                    'TCP_NODELAY': 1,
                    'TCP_KEEPIDLE': 60,
                    'TCP_KEEPINTVL': 30,
                    'TCP_KEEPCNT': 3
                }
            else:
                logger.info("🏠 Entorno local/otros - configuración estándar")
                parameters = pika.URLParameters(RABBITMQ_URL)
                parameters.heartbeat = 60
                parameters.blocked_connection_timeout = 600
                parameters.connection_attempts = 3
                parameters.retry_delay = 1
                parameters.socket_timeout = 10
            
            # SSL si es necesario
            if RABBITMQ_URL.startswith('amqps://'):
                context = ssl.create_default_context()
                parameters.ssl_options = pika.SSLOptions(context)
                logger.info("🔒 Usando conexión SSL (amqps)")
            
            # Crear conexión
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # ✨ CONFIGURACIÓN DE COLA ROBUSTA
            channel.queue_declare(
                queue=QUEUE_NAME, 
                durable=True,
                exclusive=False,
                auto_delete=False
            )
            
            # ✨ QoS MUY ESTRICTO PARA EVITAR PÉRDIDAS
            if is_railway:
                # Railway: procesamiento secuencial estricto
                channel.basic_qos(prefetch_count=1, global_qos=False)
                logger.info("🚂 Railway QoS: prefetch=1 (estricto)")
            else:
                # Local: configuración normal
                channel.basic_qos(prefetch_count=1, global_qos=True)
                logger.info("🏠 Local QoS: prefetch=1 (normal)")
            
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
    """Actualizar estado del pedido via API"""
    try:
        url = f"{ORDERS_API_URL}/api/orders/{order_id}/status"
        params = {"new_status": status}
        
        response = requests.patch(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Error actualizando pedido {order_id}: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error conectando a Orders API: {e}")
        return False


def callback(ch, method, properties, body):
    """
    ✨ Callback mejorado que se ejecuta cuando se recibe un mensaje de la cola
    """
    global message_counter, last_message_time
    
    delivery_tag = method.delivery_tag
    start_time = time.time()
    message_counter += 1
    last_message_time = start_time
    
    try:
        # Decodificar mensaje JSON
        message = json.loads(body.decode('utf-8'))
        
        order_id = message.get("order_id", "unknown")
        customer_id = message.get("customer_id", "unknown") 
        total_amount = message.get("total_amount", 0)
        products = message.get("products", [])
        
        # Log simple del pedido
        products_list = ", ".join(products) if len(products) <= 3 else f"{', '.join(products[:3])}, ..."
        logger.info(f"Nuevo pedido recibido - ID: {order_id}")
        logger.info(f"Cliente: {customer_id} | Productos: {products_list} | Total: ${total_amount}")
        
        # Esperar antes de confirmar
        time.sleep(1)
        
        # Actualizar estado
        success = update_order_status(order_id)
        
        if success:
            logger.info(f"Notificacion enviada - Pedido {order_id} confirmado")
        else:
            logger.warning(f"Pedido {order_id} procesado pero no se pudo confirmar estado")
        

        # Confirmar mensaje
        ch.basic_ack(delivery_tag=delivery_tag)
        logger.info(f"Mensaje #{message_counter} procesado correctamente")
        logger.info("")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {e}")
        ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        ch.basic_nack(delivery_tag=delivery_tag, requeue=True)


def start_consumer():
    """Iniciar consumer de notificaciones"""
    logger.info("Notifications Service iniciado")
    
    connection = None
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while True:  # ✨ Loop infinito para reconexión automática
        try:
            connection, channel = connect_to_rabbitmq()
            consecutive_errors = 0
            
            # Detectar ambiente
            is_railway = "railway.internal" in RABBITMQ_URL or "rlwy.net" in RABBITMQ_URL
            env_name = "RAILWAY" if is_railway else "LOCAL"
            
            # Configurar callback con timeout específico para Railway
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback,
                auto_ack=False  # ✨ ACK manual para control total
            )
            
            logger.info(f"Notifications Service listo - Ambiente: {env_name}")
            logger.info("Esperando pedidos...")
            
            # ✨ MONITOREO DE CONEXIÓN PARA RAILWAY
            try:
                channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker as e:
                logger.error(f"Conexión cerrada: {e}")
                consecutive_errors += 1
                raise
            except pika.exceptions.AMQPChannelError as e:
                logger.error(f"Error de canal: {e}")
                consecutive_errors += 1
                raise
            
        except KeyboardInterrupt:
            logger.info("Consumer detenido")
            break
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error en consumer: {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                logger.error("Demasiados errores - verificar configuración")
                time.sleep(30)
            else:
                logger.error(f"Reintentando en 15 segundos... ({consecutive_errors}/{max_consecutive_errors})")
                time.sleep(15)
            continue
    
    # Cierre limpio
    try:
        if connection and not connection.is_closed:
            connection.close()
        logger.info("Notifications Service finalizado")
    except:
        logger.info("Notifications Service finalizado")


if __name__ == "__main__":
    start_consumer()
