import os
import json
import pika
import pika.exceptions
import ssl
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
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
            logger.info(f"Conectando a RabbitMQ... (intento {retries + 1}/{MAX_RETRIES})")
            
            # ✨ CONFIGURACIÓN ESPECÍFICA PARA RAILWAY PROXY
            is_railway = "railway.internal" in RABBITMQ_URL or "rlwy.net" in RABBITMQ_URL
            
            # Configuración según ambiente
            parameters = pika.URLParameters(RABBITMQ_URL)
            
            if is_railway:
                # Railway: configuración conservadora para proxy
                parameters.heartbeat = 30
                parameters.blocked_connection_timeout = 120
                parameters.connection_attempts = 5
                parameters.retry_delay = 2
                parameters.socket_timeout = 15
            else:
                # Local: configuración estándar
                parameters.heartbeat = 60
                parameters.blocked_connection_timeout = 600
                parameters.connection_attempts = 3
                parameters.retry_delay = 1
                parameters.socket_timeout = 10
            
            # SSL si es necesario
            if RABBITMQ_URL.startswith('amqps://'):
                context = ssl.create_default_context()
                parameters.ssl_options = pika.SSLOptions(context)
            
            # Crear conexión
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Configuración de cola
            channel.queue_declare(
                queue=QUEUE_NAME, 
                durable=True,
                exclusive=False,
                auto_delete=False
            )
            
            # QoS: procesar 1 mensaje a la vez
            channel.basic_qos(prefetch_count=1, global_qos=False)
            
            logger.info(f"Conectado a RabbitMQ - Cola: {QUEUE_NAME}")
            
            return connection, channel
            
        except Exception as e:
            retries += 1
            logger.error(f"Error conectando a RabbitMQ: {e}")
            
            if retries < MAX_RETRIES:
                logger.info(f"Reintentando en {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Maximo de reintentos alcanzado")
                raise


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
        
        # Simular procesamiento
        time.sleep(1)
        
        logger.info(f"Notificacion procesada - Pedido {order_id}")
        
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
