# Sistema de Pedidos - Microservicios con RabbitMQ

Sistema de gestión de pedidos usando arquitectura de microservicios desacoplados mediante mensajería asíncrona (RabbitMQ).

## Descripción

Aplicación que permite gestionar pedidos a través de dos microservicios independientes:

- **Orders Service**: API REST para crear y consultar pedidos (FastAPI + MongoDB)
- **Notifications Service**: Consumidor que procesa notificaciones de pedidos desde RabbitMQ

## Tecnologías

- Python 3.11
- FastAPI
- MongoDB
- RabbitMQ (Pika)
- Docker
- Railway (deployment)

## Características

### Orders Service (API REST)
- Crear pedidos (POST)
- Listar pedidos (GET)
- Obtener pedido por ID (GET)
- Actualizar estado de pedido (PATCH)
- Validación de datos con Pydantic
- Documentación automática (Swagger)
- Publicación de eventos a RabbitMQ

### Notifications Service (Consumer)
- Consumo de mensajes desde RabbitMQ
- Procesamiento asíncrono de notificaciones
- Reconexión automática en caso de fallo
- Logs de pedidos procesados

## 🏗️ Flujo Completo con Confirmación

## Flujo de Trabajo

```
Cliente → POST /orders → Orders Service → MongoDB (guardar)
                                        → RabbitMQ (publicar)
                                        
RabbitMQ → Notifications Service → Procesar notificación
                                 → Log de confirmación
```

## Estructura del Proyecto

```
/orders_service/
├── main.py
├── routes/
│   └── orders.py
├── config/
│   ├── database.py
│   └── rabbit.py
├── models/
│   ├── order.py
│   └── responses.py
├── Dockerfile
└── requirements.txt

/notifications_service/
├── consumer.py
├── Dockerfile
└── requirements.txt

/
├── docker-compose.yml
└── .env
```

## Instalación y Uso

### Desarrollo Local con Docker Compose

1. Clonar el repositorio
```bash
git clone <repo-url>
cd Reto-2
```

2. Levantar todos los servicios (incluye RabbitMQ automáticamente)
```bash
docker-compose up -d
```

Esto levantará:
- ✅ RabbitMQ (puerto 5672 para AMQP, 15672 para UI)
- ✅ MongoDB (puerto 27018)
- ✅ Orders Service (puerto 8001)
- ✅ Notifications Service (consumer en background)

3. Verificar que todo esté funcionando
```bash
docker-compose ps
docker-compose logs -f notifications_service
```

4. Acceder a las interfaces
- API: http://localhost:8001/docs
- RabbitMQ Management: http://localhost:15672 (usuario: guest, contraseña: guest)
```

5. Probar la API
```bash
# Crear un pedido
curl -X POST "http://localhost:8001/api/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cliente_123",
    "products": ["Producto 1", "Producto 2"],
    "total_amount": 150.00
  }'

# Ver los logs del notifications service en tiempo real
docker-compose logs -f notifications_service
```

6. Detener servicios
```bash
docker-compose down
```

## ✨ REQUISITOS FUNCIONALES

### 📊 ORDERS SERVICE:
- **ENDPOINT**: `POST /api/orders`
- **BODY**: `{ "customer_id": "123", "products": [...], "total_amount": 99.99 }`
- **ACCIONES**:
  1. Guardar en MongoDB colección 'orders'
  2. Publicar mensaje JSON a cola 'orders_queue'
  3. Retornar 201 con order creado

### 🔔 NOTIFICATIONS SERVICE:
- **CONSUMER**: Escucha permanente cola 'orders_queue'
- **PROCESAMIENTO**:
  1. Recibir mensaje JSON con order_id
  2. Log en consola: "New order received: {order_id}"
  3. **⏰ ESPERAR 4 segundos** (para permitir consultas)
  4. **✨ LLAMAR API**: `PATCH /orders/{order_id}/status?new_status=notified`
  5. **✅ CONFIRMAR**: Log "NOTIFICACIÓN CONFIRMADA"
  6. Ack automático del mensaje

## 🎯 FUNCIONALIDAD EXTRA - Estado de Confirmación

### **✨ DESTACADO**: Cuando el notifications service procesa un pedido:

1. **📝 Muestra los datos completos** del pedido
2. **⏰ Espera 4 segundos** (tiempo para consultar API y ver estado "pending")
3. **📞 Llama automáticamente** al endpoint `PATCH /orders/{order_id}/status`
4. **✅ Actualiza el estado** del pedido a `"notified"`
5. **🔄 Confirma la notificación** en logs con mensaje destacado

**🎪 Resultado Visual**: Puedes hacer `GET /orders/{id}` antes y después para ver cómo el estado cambia de `"pending"` → `"notified"` ✨

## 📂 ESTRUCTURA ARCHIVOS

```
/orders_service/
├── main.py                 # App FastAPI
├── routes/
│   └── orders.py          # POST /orders + PATCH /orders/{id}/status ✨
├── config/
│   ├── database.py        # MongoDB connection
│   └── rabbit.py          # RabbitMQ publisher
├── models/
│   ├── order.py           # Order models
│   └── responses.py       # Response schemas
├── Dockerfile
└── requirements.txt

/notifications_service/
├── consumer.py            # RabbitMQ consumer + API calls ✨
├── Dockerfile
└── requirements.txt       # Pika + Requests ✨

/adicional/
├── docker-compose.yml     # Orden correcta startup
├── railway.json           # Railway config
├── Procfile              # Railway services  
└── .env                  # RABBITMQ_URL, ORDERS_API_URL ✨
```

## 🔧 CONFIGURACIÓN DOCKER COMPOSE

```yaml
version: '3.8'
services:
  orders_service:
    build: ./orders_service
    ports:
      - "8001:8000"  # FastAPI
    depends_on:
      - mongodb
    environment:
      - RABBITMQ_URL=${RABBITMQ_URL}
      - MONGODB_URL=mongodb://mongodb:27017/ordersdb
  
  notifications_service:
    build: ./notifications_service
    depends_on:
      - orders_service  # ✨ Necesita API para confirmación
    environment:
      - RABBITMQ_URL=${RABBITMQ_URL}
      - ORDERS_API_URL=http://orders_service:8000  # ✨
  
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
```

## Despliegue en Railway

1. Subir el código a GitHub
2. Crear servicios en Railway:
   - MongoDB (desde template de Railway)
   - RabbitMQ (desde template de Railway)
   - Orders Service (desde GitHub)
   - Notifications Service (desde GitHub)

3. Configurar variables de entorno en Railway:

**Para Orders Service:**
```
RABBITMQ_URL=amqp://user:pass@rabbitmq.railway.internal:5672
MONGODB_URL=<railway-mongodb-url>
```

**Para Notifications Service:**
```
RABBITMQ_URL=amqp://user:pass@rabbitmq.railway.internal:5672
```

**Importante:** Usar `rabbitmq.railway.internal` para la comunicación interna entre servicios en Railway.

## API Endpoints

### Crear Pedido
```bash
POST /api/orders/

{
  "customer_id": "customer_123",
  "products": ["Laptop", "Mouse", "Teclado"],
  "total_amount": 1299.99
  "customer_id": "cliente_123",
  "products": ["Producto 1", "Producto 2"],
  "total_amount": 150.00
}

# Respuesta:
{
  "success": true,
  "statusCode": 201,
  "message": "Pedido creado exitosamente",
  "data": {
    "_id": "68ef157f7c92023314c89617",
    "customer_id": "cliente_123",
    "products": ["Producto 1", "Producto 2"],
    "total_amount": 150.00,
    "status": "pending",
    "created_at": "2025-10-15T03:31:11.785136"
  }
}
```

### Listar Pedidos
```bash
GET /api/orders/
```

### Obtener Pedido por ID
```bash
GET /api/orders/{order_id}
```

### Actualizar Estado
```bash
PATCH /api/orders/{order_id}/status?new_status=notified
```

## Documentación API

La documentación interactiva está disponible en:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Logs de Ejemplo

### Orders Service
```
INFO: Pedido creado en MongoDB
INFO: Evento publicado a RabbitMQ
```

### Notifications Service
```
INFO: Nuevo pedido recibido - ID: 68ef157f7c92023314c89617
INFO: Cliente: cliente_123 | Productos: Producto 1, Producto 2 | Total: $150.0
INFO: Notificacion procesada - Pedido 68ef157f7c92023314c89617
```

## Notas Técnicas

- Los servicios están desacoplados completamente mediante RabbitMQ
- El notifications service se reconecta automáticamente si RabbitMQ falla
- Los mensajes se confirman (ACK) solo después de procesarse correctamente
- Para Railway, usar `rabbitmq.railway.internal` para mejor estabilidad
======================================================================
NUEVO PEDIDO RECIBIDO
Order ID:     507f1f77bcf86cd799439011
Customer ID:  demo_123
Productos:    1 item(s)
   - Demo Product
TOTAL:        $29.99
======================================================================
INFO: 🕐 Esperando 4 segundos antes de confirmar notificación...
INFO: 📡 Actualizando estado del pedido 507f1f77bcf86cd799439011 a 'notified'...
INFO: ✅ API Response: Estado actualizado exitosamente
INFO: ✅ NOTIFICACIÓN CONFIRMADA - Pedido 507f1f77bcf86cd799439011 actualizado a 'notified'
INFO: 🔄 Mensaje procesado y confirmado (ACK)
======================================================================
```

## 🚀 Deploy en Railway

### Usando el Template (Recomendado)
## Autor

Valentín Pico

## Repositorio

https://github.com/Valentinpico/Reto-2-DM