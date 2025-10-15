# 🚀 Sistema de Pedidos con Microservicios Desacoplados via RabbitMQ

**PROYECTO**: Sistema de Pedidos con Microservicios Desacoplados via RabbitMQ

## 🚂 Desplegar en Railway (1-Click)

### ⚡ Deploy Automático con Template

¡La forma MÁS FÁCIL de desplegar este proyecto!

```
https://railway.com/new/template/_o12zG
```

**Pasos:**
1. Click en el link del template
2. Conecta tu cuenta de GitHub
3. Railway desplegará automáticamente:
   - ✅ Orders Service (API REST)
   - ✅ Notifications Service (Consumer)
   - ✅ MongoDB
   - ✅ RabbitMQ interno
   - ✅ Variables de entorno configuradas
4. En 2-3 minutos tendrás tu API funcionando en la nube

**URLs después del deploy:**
- 📡 API REST: `https://tu-orders-service.up.railway.app`
- 📚 Swagger: `https://tu-orders-service.up.railway.app/docs`

---

## 🎯 ARQUITECTURA

Dos microservicios independientes que se comunican mediante mensajería asíncrona:

### 1. 📊 ORDERS SERVICE (Productor):
- API REST para crear pedidos
- Persiste en MongoDB
- Publica eventos a RabbitMQ

### 2. 🔔 NOTIFICATIONS SERVICE (Consumidor):
- Escucha cola RabbitMQ continuamente
- Procesa mensajes asincrónicamente
- **✨ EXTRA**: Actualiza estado del pedido vía API
- Sin exposición HTTP (solo consumer)

## 🏗️ Flujo Completo con Confirmación

```
┌─────────────────┐    RabbitMQ     ┌──────────────────────┐
│  Orders Service │ ───────────────▶│ Notifications Service│
│   (Producer)    │   orders_queue  │     (Consumer)       │
│                 │                 │                      │
│ 1. Crear pedido │                 │ 3. Procesar mensaje  │
│ 2. Publicar     │                 │ 4. Esperar 4s ⏰     │
│    evento       │                 │ 5. Llamar API ───────┐
│                 │ ◀───────────────│    PATCH /status     │
│ 6. Actualizar   │  HTTP Request   │ 6. Confirmar ✅      │
│    a "notified" │                 │                      │
└─────────────────┘                 └──────────────────────┘
```

## 🛠️ STACK TECNOLÓGICO COMÚN

- **FastAPI** (solo orders service)
- **MongoDB** (solo orders service) 
- **RabbitMQ** (ambos servicios)
- **Pika** para RabbitMQ + **Requests** para HTTP
- **Docker + Docker Compose**
- **Railway** (despliegue en nube)

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

## 📋 FORMATO MENSAJE RABBITMQ

```json
{
  "order_id": "507f1f77bcf86cd799439011",
  "customer_id": "12345",
  "total_amount": 99.99,
  "products": ["Producto A", "Producto B"],
  "timestamp": "2024-01-01T10:30:00Z"
}
```

## 🌍 VARIABLES ENTORNO

```bash
# Railway RabbitMQ (funciona local + producción)
RABBITMQ_URL=amqp://user:pass@switchback.proxy.rlwy.net:34368

# MongoDB
MONGODB_URL=mongodb://mongodb:27017/ordersdb

# ✨ API Communication (NUEVO)
ORDERS_API_URL=http://orders_service:8000  # Docker interno
# ORDERS_API_URL=https://tu-orders.up.railway.app  # Railway
```

## 📡 API Endpoints

### 📊 Orders Service

#### 🆕 Crear pedido
```bash
POST /api/orders/
Content-Type: application/json

{
  "customer_id": "customer_123",
  "products": ["Laptop", "Mouse", "Teclado"],
  "total_amount": 1299.99
}
```

#### 📋 Listar todos los pedidos
```bash
GET /api/orders/
```

#### 🔍 Obtener pedido específico
```bash
GET /api/orders/{order_id}
```

#### ✨ Actualizar estado del pedido (NUEVO)
```bash
PATCH /api/orders/{order_id}/status?new_status=notified
```

**Estados disponibles:**
- `pending`: Pedido creado, esperando procesamiento
- `notified`: Notificación enviada y confirmada ✅
- `processing`: En procesamiento
- `completed`: Completado
- `cancelled`: Cancelado

## ⚡ Comandos Rápidos (Desarrollo Local)

### Inicio Rápido (Railway RabbitMQ)
```bash
# 1. Configurar variables de entorno
export RABBITMQ_URL="amqp://user:pass@switchback.proxy.rlwy.net:34368"

# 2. Levantar servicios
docker-compose up --build -d

# 3. Ver logs con confirmaciones ✨
docker-compose logs -f notifications_service | grep -E "(✅|🔄|📞)"

# 4. Abrir API
open http://localhost:8001/docs
```

### Demo del Flujo Completo ✨
```bash
# 1. Crear un pedido
curl -X POST "http://localhost:8001/api/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo_123",
    "products": ["Demo Product"],
    "total_amount": 29.99
  }'

# 2. Copiar el order_id de la respuesta
# 3. Ver estado inicial (debe ser "pending")
curl "http://localhost:8001/api/orders/{order_id}"

# 4. Esperar 4-5 segundos y consultar de nuevo
# 5. Ver estado actualizado (debe ser "notified") ✅
curl "http://localhost:8001/api/orders/{order_id}"
```

## 🎯 CRITERIOS EVALUACIÓN

- ✅ Comunicación RabbitMQ funcional
- ✅ Servicios totalmente desacoplados
- ✅ Manejo de errores en conexiones
- ✅ Logs claros de flujo completo
- ✅ Despliegue independiente en Railway
- ✅ **EXTRA**: Confirmación de notificación con actualización de estado
- ✅ **EXTRA**: Delay de 4 segundos para verificación visual
- ✅ **EXTRA**: Comunicación bidireccional (RabbitMQ + HTTP)

## 🔄 Logs Esperados

### Orders Service
```
INFO: Pedido creado en MongoDB: 507f1f77bcf86cd799439011
INFO: 📡 Evento publicado a RabbitMQ exitosamente
```

### Notifications Service
```
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
1. Ve a: `https://railway.com/new/template/_o12zG`
2. Conecta GitHub
3. ¡Listo! 🎉

### Deploy Manual
```bash
# 1. Subir a GitHub
git add .
git commit -m "feat: sistema completo con confirmación de notificaciones"
git push origin main

# 2. En Railway:
# - New Project → GitHub Repo
# - Agregar servicios: orders_service, notifications_service
# - MongoDB: Add → Database → MongoDB
# - RabbitMQ: Add → Database → RabbitMQ
```

---

## 💡 Características Destacadas

### 🔄 **Comunicación Bidireccional**
- **RabbitMQ**: Orders → Notifications (async)
- **HTTP REST**: Notifications → Orders (sync)

### ⏰ **Timing Perfecto**
- 4 segundos de delay para verificación visual
- Logs claros con emojis para seguimiento

### 🎯 **Estados Dinámicos**
- `pending` → `notified` automáticamente
- Confirmación visual en tiempo real

### 🛡️ **Tolerancia a Fallos**
- Reintentos automáticos en RabbitMQ
- Manejo de errores HTTP
- Logs detallados para debugging

¡El sistema está listo para producción en Railway! 🚀