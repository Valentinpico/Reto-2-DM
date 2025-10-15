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

# ✨ CONTADORES PARA DEBUGGING
message_counter = 0
last_message_time = None


def connect_to_rabbitmq():
    """Conectar a RabbitMQ con configuración optimizada para producción"""
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            logger.info(f"🔄 Intentando conectar a RabbitMQ... (intento {retries + 1}/{MAX_RETRIES})")
            
            # Parsear URL
            parameters = pika.URLParameters(RABBITMQ_URL)
            
            # ✨ CONFIGURACIÓN OPTIMIZADA PARA PRODUCCIÓN
            parameters.heartbeat = 60  # Aumentado para Railway
            parameters.blocked_connection_timeout = 600  # 10 minutos
            parameters.connection_attempts = 3
            parameters.retry_delay = 1
            parameters.socket_timeout = 10
            
            # Si la URL usa amqps://, configurar SSL
            if RABBITMQ_URL.startswith('amqps://'):
                context = ssl.create_default_context()
                parameters.ssl_options = pika.SSLOptions(context)
                logger.info("🔒 Usando conexión SSL (amqps)")
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # ✨ CONFIGURACIÓN MEJORADA DE COLA
            # Declarar cola con persistencia
            channel.queue_declare(
                queue=QUEUE_NAME, 
                durable=True,  # Cola persistente
                exclusive=False,  # No exclusiva
                auto_delete=False  # No auto-delete
            )
            
            # ✨ CONFIGURACIÓN QoS OPTIMIZADA
            # Procesar 1 mensaje a la vez y confirmar antes del siguiente
            channel.basic_qos(prefetch_count=1, global_qos=True)
            
            logger.info(f"✅ Conectado a RabbitMQ exitosamente")
            logger.info(f"👂 Escuchando cola: '{QUEUE_NAME}' (QoS=1)")
            
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
    ✨ Callback mejorado que se ejecuta cuando se recibe un mensaje de la cola
    """
    global message_counter, last_message_time
    
    delivery_tag = method.delivery_tag
    start_time = time.time()
    message_counter += 1
    last_message_time = start_time
    
    try:
        # ✨ LOGGING INMEDIATO CON CONTADOR
        logger.info(f"🔔 [MENSAJE #{message_counter}] Recibido - iniciando procesamiento...")
        
        # Decodificar mensaje JSON
        message = json.loads(body.decode('utf-8'))
        
        order_id = message.get("order_id", "unknown")
        customer_id = message.get("customer_id", "unknown") 
        total_amount = message.get("total_amount", 0)
        products = message.get("products", [])
        
        # ✨ LOG MEJORADO CON TIMESTAMP
        logger.info("=" * 80)
        logger.info("🆕 NUEVO PEDIDO RECIBIDO")
        logger.info(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🆔 Order ID:     {order_id}")
        logger.info(f"👤 Customer ID:  {customer_id}")
        logger.info(f"📦 Productos:    {len(products)} item(s)")
        for idx, product in enumerate(products, 1):
            logger.info(f"    {idx}. {product}")
        logger.info(f"💰 TOTAL:        ${total_amount}")
        logger.info("=" * 80)
        
        # ✨ FUNCIONALIDAD EXTRA: Actualizar estado del pedido
        logger.info("🕐 [DELAY] Esperando 1 segundo antes de confirmar notificación...")
        time.sleep(1)  # Dar tiempo para consultar el estado
        
        # ✨ LLAMADA API CON MEJOR LOGGING
        logger.info("📞 [API CALL] Iniciando actualización de estado...")
        success = update_order_status(order_id)
        
        if success:
            logger.info("🎉 ✅ NOTIFICACIÓN CONFIRMADA - Estado actualizado exitosamente!")
            logger.info(f"✨ Pedido {order_id} → Status: 'notified'")
        else:
            logger.warning("⚠️  Notificación procesada pero no se pudo actualizar estado")
        

        ch.basic_ack(delivery_tag=delivery_tag)
        processing_time = time.time() - start_time
        logger.info(f"✅ [ACK] Mensaje confirmado (procesado en {processing_time:.2f}s)")
        logger.info("🔄 [READY] Listo para siguiente mensaje")
        logger.info("=" * 80)
        logger.info("🔄 [READY] Listo para siguiente mensaje")
        logger.info("=" * 80)

    except json.JSONDecodeError as e:
        processing_time = time.time() - start_time
        logger.error("❌ [ERROR] Error decodificando JSON")
        logger.error(f"📍 Detalle: {e}")
        logger.error(f"📄 Mensaje recibido: {body}")
        logger.error(f"⏱️  Tiempo transcurrido: {processing_time:.2f}s")
        
        # NACK sin requeue para mensajes malformados
        ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
        logger.error("❌ [NACK] Mensaje descartado (malformado)")
        logger.info("=" * 80)
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error("💥 [ERROR] Error inesperado procesando mensaje")
        logger.error(f"📍 Detalle: {e}")
        logger.error(f"⏱️  Tiempo transcurrido: {processing_time:.2f}s")
        
        # NACK con requeue para otros errores
        ch.basic_nack(delivery_tag=delivery_tag, requeue=True)
        logger.error("🔄 [NACK] Mensaje devuelto a la cola para reintento")
        logger.info("=" * 80)


def start_consumer():
    """✨ Iniciar el consumer de RabbitMQ con reconexión automática"""
    logger.info("🚀 Notifications Service iniciado")
    logger.info("⏳ Esperando mensajes de pedidos...")
    
    connection = None
    
    while True:  # ✨ Loop infinito para reconexión automática
        try:
            logger.info("🔌 [CONNECT] Estableciendo conexión...")
            connection, channel = connect_to_rabbitmq()
            
            # ✨ CONFIGURACIÓN CONSUMER OPTIMIZADA
            logger.info("⚙️  [CONFIG] Configurando consumer...")
            
            # Comenzar a consumir mensajes
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback,
                auto_ack=False  # ✨ ACK manual para control total
            )
            
            logger.info("🎯 [READY] Consumer activo - procesando mensajes...")
            logger.info("🔥 [STATUS] Sistema listo para recibir pedidos")
            logger.info("💡 [INFO] Presiona CTRL+C para detener")
            logger.info("=" * 80)
            
            # ✨ CONSUMO CON MANEJO DE RECONEXIÓN
            channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("")
            logger.info("⏹️  [STOP] Consumer detenido por el usuario")
            break
            
        except Exception as e:
            logger.error(f"💥 [FATAL] Error en el consumer: {e}")
            logger.error("🔄 [RECONNECT] Intentando reconectar en 10 segundos...")
            time.sleep(10)
            continue
    
    # ✨ CIERRE LIMPIO DE CONEXIÓN
    try:
        if connection and not connection.is_closed:
            logger.info("🔌 [DISCONNECT] Cerrando conexión...")
            connection.close()
        logger.info("👋 [EXIT] Notifications Service finalizado")
    except:
        logger.info("👋 [EXIT] Notifications Service finalizado (forzado)")


if __name__ == "__main__":
    start_consumer()
