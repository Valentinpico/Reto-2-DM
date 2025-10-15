# 🚂 Guía de Despliegue en Railway

Esta guía te ayudará a desplegar los microservicios en Railway de forma independiente.

## 📋 Prerequisitos

- Cuenta en [Railway](https://railway.app/)
- Cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (gratis) o usar Railway MongoDB
- CLI de Railway instalado (opcional): `npm i -g @railway/cli`

## 🏗️ Arquitectura de Despliegue

```
Railway Project: Orders System
├── Service 1: Orders Service (FastAPI)
├── Service 2: Notifications Service (Consumer)
├── Service 3: RabbitMQ (CloudAMQP)
└── MongoDB Atlas (externo) o Railway MongoDB
```

## 📦 Paso 1: Preparar MongoDB

### Opción A: MongoDB Atlas (Recomendado - Gratis)

1. Crear cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crear un cluster gratuito (M0)
3. Crear un usuario de base de datos
4. Whitelist todas las IPs: `0.0.0.0/0`
5. Copiar la connection string:
   ```
   mongodb+srv://usuario:password@cluster.mongodb.net/ordersdb?retryWrites=true&w=majority
   ```

### Opción B: Railway MongoDB Plugin

1. En Railway, agregar plugin "MongoDB"
2. Copiar la variable `MONGO_URL` que se genera automáticamente

## 📦 Paso 2: Configurar RabbitMQ

### Opción A: CloudAMQP (Recomendado - Gratis)

1. Ir a [CloudAMQP](https://www.cloudamqp.com/)
2. Crear cuenta gratuita
3. Crear nueva instancia (Plan: Little Lemur - Free)
4. Copiar la AMQP URL:
   ```
   amqp://usuario:password@servidor.cloudamqp.com/vhost
   ```

### Opción B: Railway (Requiere pago)

Railway no tiene RabbitMQ gratuito, pero puedes usar:
- CloudAMQP (gratis hasta 1M mensajes/mes)
- RabbitMQ Cloud (gratis hasta 100 conexiones)

## 📦 Paso 3: Desplegar Orders Service

### Desde la interfaz web de Railway:

1. **Crear nuevo proyecto** en Railway
2. **Add Service** → **GitHub Repo**
3. Seleccionar tu repositorio
4. **Settings**:
   - **Root Directory**: `/orders_service` (importante!)
   - **Build Command**: (dejar vacío, usa Dockerfile)
   - **Start Command**: (dejar vacío, usa Dockerfile)

5. **Variables de entorno**:
   ```
   MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/ordersdb
   RABBITMQ_URL=amqp://usuario:password@servidor.cloudamqp.com/vhost
   PORT=8000
   ```

6. **Deploy** automático
7. **Generar dominio público**: Settings → Generate Domain
8. Copiar la URL: `https://tu-proyecto.railway.app`

### Desde CLI:

```bash
cd orders_service
railway login
railway init
railway up
railway variables set MONGODB_URL="tu-mongodb-url"
railway variables set RABBITMQ_URL="tu-rabbitmq-url"
railway open
```

## 📦 Paso 4: Desplegar Notifications Service

### Desde la interfaz web de Railway:

1. En el mismo proyecto, **Add Service** → **GitHub Repo**
2. Seleccionar el mismo repositorio
3. **Settings**:
   - **Root Directory**: `/notifications_service` (importante!)
   - **Build Command**: (dejar vacío, usa Dockerfile)
   - **Start Command**: (dejar vacío, usa Dockerfile)

4. **Variables de entorno**:
   ```
   RABBITMQ_URL=amqp://usuario:password@servidor.cloudamqp.com/vhost
   ```

5. **Deploy** automático

### Desde CLI:

```bash
cd notifications_service
railway link  # Seleccionar el mismo proyecto
railway up
railway variables set RABBITMQ_URL="tu-rabbitmq-url"
```

## 🔍 Paso 5: Verificar el Despliegue

### Orders Service:
```bash
# Health check
curl https://tu-orders-service.railway.app/

# Crear pedido
curl -X POST https://tu-orders-service.railway.app/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_123",
    "products": [{"product_id": "1", "name": "Test", "quantity": 1, "price": 99.99}],
    "total_amount": 99.99
  }'
```

### Notifications Service:
```bash
# Ver logs en Railway
railway logs -s notifications_service

# Deberías ver:
# 📬 NUEVO PEDIDO RECIBIDO
# 🆔 Order ID: xxx
```

### RabbitMQ Management:
- CloudAMQP: https://www.cloudamqp.com/console
- Ver la cola `orders_queue`
- Verificar mensajes procesados

## 📝 Variables de Entorno Completas

### Orders Service:
```env
MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/ordersdb
RABBITMQ_URL=amqp://usuario:password@servidor.cloudamqp.com/vhost
PORT=8000
```

### Notifications Service:
```env
RABBITMQ_URL=amqp://usuario:password@servidor.cloudamqp.com/vhost
```

## 🎯 Consejos Pro

1. **Naming**: Nombra bien tus servicios en Railway
   - `orders-service-prod`
   - `notifications-service-prod`

2. **Logs**: Usa Railway logs para debug
   ```bash
   railway logs -s orders-service
   railway logs -s notifications-service
   ```

3. **Domains**: Asigna custom domain (opcional)
   - Settings → Custom Domain

4. **Monitoring**: 
   - CloudAMQP dashboard para RabbitMQ
   - MongoDB Atlas dashboard para DB
   - Railway logs para servicios

5. **Escalabilidad**:
   - Railway escala automáticamente
   - CloudAMQP free tier: 1M msgs/mes
   - MongoDB Atlas free tier: 512MB storage

## 🚨 Troubleshooting

### Error: "Connection refused" en RabbitMQ
- Verificar que RABBITMQ_URL esté correcta
- Verificar que CloudAMQP esté activo
- Check logs: `railway logs -s notifications-service`

### Error: "Cannot connect to MongoDB"
- Verificar MONGODB_URL
- Verificar IP whitelist en Atlas (debe ser 0.0.0.0/0)
- Verificar usuario/password

### Notifications no recibe mensajes
- Verificar que ambos servicios usen el mismo RABBITMQ_URL
- Verificar logs del consumer
- Verificar cola en CloudAMQP dashboard

### Service crashea
- Ver logs: `railway logs`
- Verificar Dockerfile
- Verificar variables de entorno

## 📊 Estructura Final en Railway

```
Project: Orders System
│
├── orders-service (Web Service)
│   ├── URL: https://orders-xxx.railway.app
│   ├── Root: /orders_service
│   └── Vars: MONGODB_URL, RABBITMQ_URL
│
├── notifications-service (Background Worker)
│   ├── Root: /notifications_service
│   └── Vars: RABBITMQ_URL
│
└── External Services:
    ├── MongoDB Atlas (free)
    └── CloudAMQP (free)
```

## 💰 Costos

- **Railway**: $5/mes crédito gratuito (suficiente para hobby)
- **MongoDB Atlas**: Free tier M0 (512MB)
- **CloudAMQP**: Free tier (1M mensajes/mes)

**Total**: $0 - $5/mes dependiendo del uso

## 🎉 ¡Listo!

Tu sistema de microservicios está desplegado y funcionando en Railway.

**URLs importantes:**
- API Docs: `https://tu-orders-service.railway.app/docs`
- RabbitMQ Dashboard: CloudAMQP console
- MongoDB Dashboard: MongoDB Atlas console
- Railway Dashboard: https://railway.app/project/tu-proyecto

---

**¿Necesitas ayuda?** Revisa los logs con `railway logs` o contacta al equipo.
