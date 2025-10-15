# 🚀 Sistema de Pedidos con Microservicios + RabbitMQ

Arquitectura de microservicios desacoplados usando mensajería asíncrona con RabbitMQ. Este proyecto implementa un sistema de pedidos donde el servicio de órdenes publica eventos que son consumidos por el servicio de notificaciones.

## 🏗️ Arquitectura

```
┌─────────────────┐      ┌──────────────┐      ┌──────────────────────┐
│  Orders Service │─────▶│   RabbitMQ   │─────▶│ Notifications Service│
│   (Producer)    │      │    (Broker)  │      │     (Consumer)       │
│   Port: 8001    │      │  Port: 5672  │      │   (Background)       │
└─────────────────┘      └──────────────┘      └──────────────────────┘
        │                       │                           │
        ▼                       ▼                           ▼
  ┌──────────┐          [Management UI]              [Logs/Email]
  │ MongoDB  │           Port: 15672
  │Port:27018│
  └──────────┘
```

### Servicios:

1. **Orders Service** (Productor):
   - API REST con FastAPI
   - Guarda pedidos en MongoDB
   - Publica eventos a RabbitMQ
   - Puerto: 8001

2. **Notifications Service** (Consumidor):
   - Consumer Python puro (sin HTTP)
   - Escucha cola RabbitMQ continuamente
   - Procesa notificaciones de pedidos
   - Logging de eventos

## 🛠️ Stack Tecnológico

- **FastAPI** - Framework web moderno y rápido
- **MongoDB** - Base de datos NoSQL para pedidos
- **RabbitMQ** - Message broker para comunicación asíncrona
- **Pika** - Cliente Python para RabbitMQ
- **Motor** - Driver asíncrono de MongoDB
- **Docker + Docker Compose** - Containerización
- **Pydantic V2** - Validación de datos

## 📁 Estructura del Proyecto

```
Reto-2/
├── orders_service/              # Microservicio de pedidos
│   ├── main.py                 # App FastAPI
│   ├── models/
│   │   ├── order.py           # Modelos de pedidos
│   │   └── responses.py       # Modelos de respuesta
│   ├── routes/
│   │   └── orders.py          # Endpoints CRUD de pedidos
│   ├── config/
│   │   ├── database.py        # Conexión MongoDB
│   │   └── rabbit.py          # Publisher RabbitMQ
│   ├── utils/
│   │   ├── exceptions.py      # Excepciones personalizadas
│   │   ├── middleware.py      # Manejadores de errores
│   │   └── response.py        # Respuestas estandarizadas
│   ├── Dockerfile
│   └── requirements.txt
│
├── notifications_service/       # Microservicio de notificaciones
│   ├── consumer.py             # Consumer RabbitMQ
│   ├── config/
│   │   └── rabbit.py          # Config RabbitMQ
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml          # Orquestación de servicios
├── .env.example               # Variables de entorno de ejemplo
├── .gitignore
└── README.md
```

## 🚀 Cómo Ejecutar

Tienes **DOS OPCIONES** para ejecutar RabbitMQ:

### 🐳 OPCIÓN 1: RabbitMQ en Docker (Todo containerizado)

Esta opción levanta **TODO** en Docker Compose (MongoDB, RabbitMQ, Orders Service, Notifications Service).

```bash
# 1. Ir al directorio del proyecto
cd Reto-2

# 2. Levantar TODOS los servicios (incluyendo RabbitMQ en Docker)
docker-compose --profile docker-rabbit up --build -d

# 3. Ver logs de todos los servicios
docker-compose logs -f

# 4. Ver logs solo del notifications service
docker-compose logs -f notifications_service

# Para detener todo
docker-compose --profile docker-rabbit down

# Para detener y eliminar volúmenes
docker-compose --profile docker-rabbit down -v
```

**Servicios disponibles:**
- 📡 Orders API: http://localhost:8001
- 📚 Swagger Docs: http://localhost:8001/docs
- 🐰 RabbitMQ Management: http://localhost:15672 (user: `guest`, pass: `guest`)
- 🍃 MongoDB: localhost:27018

---

### 💻 OPCIÓN 2: RabbitMQ Local (Recomendado para desarrollo)

Esta opción usa RabbitMQ instalado localmente en tu Mac con Homebrew, mientras que MongoDB y los servicios corren en Docker.

#### Paso 1: Instalar RabbitMQ local

```bash
# Instalar RabbitMQ con Homebrew
brew install rabbitmq

# Iniciar RabbitMQ como servicio en background
brew services start rabbitmq

# O iniciarlo manualmente
rabbitmq-server &

# Verificar que está corriendo
brew services list | grep rabbitmq
```

#### Paso 2: Levantar servicios en Docker

```bash
# Levantar MongoDB y los servicios (sin RabbitMQ)
docker-compose up --build -d

# Ver logs en tiempo real
docker-compose logs -f

# Ver solo notifications service
docker-compose logs -f notifications_service
```

#### Paso 3: Verificar conexión

```bash
# Verificar RabbitMQ local
curl http://localhost:15672/api/overview -u guest:guest

# Ver estado de contenedores
docker-compose ps
```

**Servicios disponibles:**
- 📡 Orders API: http://localhost:8001
- 📚 Swagger Docs: http://localhost:8001/docs
- 🐰 RabbitMQ Management (LOCAL): http://localhost:15672 (user: `guest`, pass: `guest`)
- 🍃 MongoDB: localhost:27018

**Para detener:**
```bash
# Detener servicios Docker
docker-compose down

# Detener RabbitMQ local
brew services stop rabbitmq
```

---

### 🤔 ¿Cuál opción usar?

| Característica | Docker | Local (Homebrew) |
|---------------|--------|------------------|
| **Setup** | Automático, solo `docker-compose up` | Requiere instalar RabbitMQ con `brew install rabbitmq` |
| **Portabilidad** | ✅ Funciona igual en todos los sistemas | ⚠️ Solo macOS/Linux con Homebrew |
| **Performance** | Bueno (virtualización) | ⭐ Mejor (nativo) |
| **Logs** | `docker-compose logs rabbitmq` | `tail -f /opt/homebrew/var/log/rabbitmq/...` |
| **Management UI** | http://localhost:15672 | http://localhost:15672 |
| **Persistencia** | Volume Docker | Disco local |
| **Uso de RAM** | ~200MB | ~150MB |
| **Recomendado para** | Producción, CI/CD, equipos | Desarrollo local, aprendizaje |

**Recomendación:** 
- 🐳 Usa **Docker** si trabajas en equipo o vas a deployar
- 💻 Usa **Local** si estás aprendiendo RabbitMQ y quieres tener control total

### Opción 2: Local (Desarrollo)

#### Requisitos previos:
- Python 3.11+
- MongoDB corriendo
- RabbitMQ corriendo

```bash
# Terminal 1 - Orders Service
cd orders_service
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
export MONGODB_URL=mongodb://localhost:27017/ordersdb
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/
uvicorn main:app --reload --port 8001

# Terminal 2 - Notifications Service
cd notifications_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/
python consumer.py
```

## 📡 API Endpoints

### Orders Service

#### Health Check
```bash
GET /
GET /health
```

#### Listar todos los pedidos
```bash
GET /api/orders/
```

#### Obtener pedido por ID
```bash
GET /api/orders/{order_id}
```

#### Crear pedido
```bash
POST /api/orders/
```

## 📝 Ejemplos de Uso

### 1. Crear un Pedido

#### cURL
```bash
curl -X POST http://localhost:8001/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "Valentin",
    "products": ["Laptop Dell XPS 15", "Mouse Logitech MX Master", "Teclado Mecánico"],
    "total_amount": 1500.0
  }'
```

#### Respuesta
```json
{
  "success": true,
  "statusCode": 201,
  "message": "Pedido creado exitosamente",
  "data": {
    "_id": "68eeeabb6c16d26f6953ab6e",
    "customer_id": "Valentin",
    "products": [
      "Laptop Dell XPS 15",
      "Mouse Logitech MX Master",
      "Teclado Mecánico"
    ],
    "total_amount": 1500.0,
    "status": "pending",
    "created_at": "2025-10-15T00:28:43.123456"
  }
}
```

#### Lo que sucede internamente:
1. ✅ El pedido se guarda en MongoDB
2. 📤 Se publica un mensaje a RabbitMQ con:
```json
{
  "order_id": "68eeeabb6c16d26f6953ab6e",
  "customer_id": "Valentin",
  "products": ["Laptop Dell XPS 15", "Mouse Logitech MX Master", "Teclado Mecánico"],
  "total_amount": 1500.0,
  "timestamp": "2025-10-15T00:28:43.123456"
}
```
3. 📬 El Notifications Service recibe el mensaje y lo procesa
4. 📝 Se imprime en los logs del consumer (output real):
```
======================================================================
NUEVO PEDIDO RECIBIDO
Order ID:     68eeeabb6c16d26f6953ab6e
Customer ID:  Valentin
Productos:    3 item(s)
   - Laptop Dell XPS 15
   - Mouse Logitech MX Master
   - Teclado Mecánico
TOTAL:        $1500.0
======================================================================
Mensaje procesado y confirmado (ACK)
```

### 2. Listar Todos los Pedidos

#### cURL
```bash
curl http://localhost:8001/api/orders/
```

#### Respuesta
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Se encontraron 2 pedidos",
  "data": [
    {
      "_id": "68eeeabb6c16d26f6953ab6e",
      "customer_id": "Valentin",
      "products": ["Laptop Dell XPS 15", "Mouse Logitech MX Master", "Teclado Mecánico"],
      "total_amount": 1500.0,
      "status": "pending",
      "created_at": "2025-10-15T00:28:43.123456"
    }
  ],
  "count": 1
}
```

### 3. Obtener Pedido por ID

#### cURL
```bash
curl http://localhost:8001/api/orders/68eeeabb6c16d26f6953ab6e
```

## 🔍 Verificar el Flujo Completo

### Ver logs en tiempo real:
```bash
# Todos los servicios
docker-compose logs -f

# Solo notifications
docker-compose logs -f notifications_service

# Solo orders
docker-compose logs -f orders_service
```

### Acceder a RabbitMQ Management UI:
1. Abrir http://localhost:15672
2. Login: `guest` / `guest`
3. Ir a "Queues" y ver la cola `orders_queue`
4. Ver mensajes procesados, rate, etc.

### Acceder a MongoDB:
```bash
# Con mongosh
mongosh mongodb://localhost:27017/ordersdb

# Ver colecciones
show collections

# Ver pedidos
db.orders.find().pretty()
```

## 📊 Formato de Respuestas

Todas las respuestas siguen este formato estandarizado:

### ✅ Respuesta Exitosa
```json
{
  "success": true,
  "statusCode": 200,
  "message": "Operación exitosa",
  "data": { /* objeto o array */ },
  "count": 1  // Solo si data es un array
}
```

### ❌ Respuesta de Error
```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pedido no encontrado con identificador: 123abc",
  "data": {
    "resource": "Pedido",
    "identifier": "123abc"
  }
}
```

## 🔐 Variables de Entorno

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017/ordersdb

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

## 🛡️ Características

### Orders Service:
- ✅ Validación automática con Pydantic
- ✅ Respuestas estandarizadas
- ✅ Manejo de errores personalizado
- ✅ Logging detallado con emojis
- ✅ Middleware de tiempo de respuesta
- ✅ Health checks
- ✅ Documentación Swagger automática

### Notifications Service:
- ✅ Consumer robusto con reintentos
- ✅ ACK manual de mensajes
- ✅ Logging detallado de eventos
- ✅ Manejo de errores JSON
- ✅ Reconexión automática

### RabbitMQ:
- ✅ Colas persistentes (durable=True)
- ✅ Mensajes persistentes (delivery_mode=2)
- ✅ Prefetch para control de flujo
- ✅ Management UI incluida

## 🧪 Testing

### Probar el flujo completo:

```bash
# 1. Crear un pedido
curl -X POST http://localhost:8001/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_123",
    "products": [
      {
        "product_id": "test_prod",
        "name": "Test Product",
        "quantity": 1,
        "price": 99.99
      }
    ],
    "total_amount": 99.99
  }'

# 2. Ver los logs del notifications service
docker-compose logs notifications_service

# 3. Verificar en MongoDB
mongosh mongodb://localhost:27017/ordersdb --eval "db.orders.find().pretty()"

# 4. Ver en RabbitMQ Management
# Abrir http://localhost:15672
```

## 🐛 Troubleshooting

### El consumer no se conecta a RabbitMQ:
- Verificar que RabbitMQ esté corriendo: `docker-compose ps`
- Ver logs: `docker-compose logs rabbitmq`
- El consumer reintenta 10 veces con delay de 5s

### Los mensajes no llegan al consumer:
- Verificar que la cola existe en RabbitMQ Management
- Ver logs del orders_service: `docker-compose logs orders_service`
- Verificar que el mensaje se publicó correctamente

### Error de conexión a MongoDB:
- Verificar que MongoDB esté corriendo: `docker-compose ps`
- Ver logs: `docker-compose logs mongodb`

## 📚 Recursos Adicionales

- **Documentación API**: http://localhost:8001/docs
- **RabbitMQ Management**: http://localhost:15672
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **RabbitMQ Tutorials**: https://www.rabbitmq.com/tutorials
- **Pika Docs**: https://pika.readthedocs.io

## 💡 Próximos Pasos / Mejoras

- [ ] Agregar autenticación JWT
- [ ] Implementar dead letter queue para mensajes fallidos
- [ ] Agregar métricas con Prometheus
- [ ] Implementar rate limiting
- [ ] Agregar tests unitarios y de integración
- [ ] Deploy a Railway/Render
- [ ] Agregar envío real de emails/SMS
- [ ] Implementar retry policy en el consumer
- [ ] Agregar circuit breaker

---

## ⚡ Comandos Rápidos

### Inicio Rápido (RabbitMQ Local)
```bash
# 1. Iniciar RabbitMQ
brew services start rabbitmq

# 2. Levantar servicios
docker-compose up --build -d

# 3. Ver logs
docker-compose logs -f notifications_service

# 4. Abrir APIs
open http://localhost:8001/docs        # Swagger
open http://localhost:15672            # RabbitMQ Management
```

### Inicio Rápido (Todo en Docker)
```bash
# Levantar TODO
docker-compose --profile docker-rabbit up --build -d

# Ver logs
docker-compose logs -f

# Abrir APIs
open http://localhost:8001/docs
open http://localhost:15672
```

### Crear un Pedido de Prueba
```bash
curl -X POST http://localhost:8001/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_user",
    "products": ["Laptop", "Mouse", "Teclado"],
    "total_amount": 1999.99
  }'
```

### Ver los Logs de Notificaciones
```bash
docker-compose logs --tail=20 notifications_service
```

**Output esperado:**
```
notifications_service  | 2025-10-15 00:40:44,028 - __main__ - INFO - ======================================================================
notifications_service  | 2025-10-15 00:40:44,028 - __main__ - INFO - NUEVO PEDIDO RECIBIDO
notifications_service  | 2025-10-15 00:40:44,028 - __main__ - INFO - Order ID:     68eeed8c6c16d26f6953ab6f
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO - Customer ID:  Valentin_Final_Test
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO - Productos:    3 item(s)
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO -    - MacBook Pro 16
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO -    - Magic Mouse
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO -    - Magic Keyboard
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO - TOTAL:        $3499.99
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO - ======================================================================
notifications_service  | 2025-10-15 00:40:44,029 - __main__ - INFO - Mensaje procesado y confirmado (ACK)
```

### Detener Todo
```bash
# Docker
docker-compose down

# RabbitMQ local
brew services stop rabbitmq
```

📖 **Para más comandos útiles**, ver [COMANDOS.md](./COMANDOS.md)

---

## 🤖 Script de Ayuda (rabbitmq-helper.sh)

Incluimos un script interactivo para facilitar la gestión de RabbitMQ:

```bash
# Ver ayuda
./rabbitmq-helper.sh help

# Cambiar a RabbitMQ local
./rabbitmq-helper.sh local

# Cambiar a RabbitMQ en Docker
./rabbitmq-helper.sh docker

# Ver estado de servicios
./rabbitmq-helper.sh status

# Ver logs
./rabbitmq-helper.sh logs

# Crear pedido de prueba
./rabbitmq-helper.sh test

# Detener todo
./rabbitmq-helper.sh stop
```

---

**Hecho por Valentin Pico** 🚀

**Proyecto de aprendizaje:** Microservicios desacoplados con mensajería asíncrona
