from fastapi import APIRouter, status
from typing import Dict, Any
from datetime import datetime
from bson import ObjectId

from models.order import OrderCreate, OrderResponse
from models.responses import (
    OrderResponseModel,
    OrderListResponseModel,
    OrderCreateResponseModel,
    ErrorResponseModel
)
from config.database import get_database
from config.rabbit import publish_order_event
from utils.exceptions import (
    NotFoundException,
    BadRequestException,
    InternalServerException
)
from utils.response import success_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get(
    "/",
    response_model=OrderListResponseModel,
    responses={
        200: {
            "description": "Lista de pedidos obtenida exitosamente",
            "model": OrderListResponseModel
        }
    }
)
async def get_all_orders() -> Dict[str, Any]:
    """
    Obtener todos los pedidos
    """
    db = get_database()
    
    try:
       
        orders_cursor = db.orders.find({}).sort("created_at", -1)
        orders = await orders_cursor.to_list(length=None)
    
        for order in orders:
            order["_id"] = str(order["_id"])
            if "created_at" in order:
                order["created_at"] = order["created_at"].isoformat()
        
        logger.info(f"📋 Se encontraron {len(orders)} pedidos")
        
        return success_response(
            data=orders,
            message=f"Se encontraron {len(orders)} pedidos"
        )
    except Exception as e:
        logger.error(f"Error obteniendo pedidos: {e}")
        raise InternalServerException("Error al obtener los pedidos")


@router.get(
    "/{order_id}",
    response_model=OrderResponseModel,
    responses={
        200: {
            "description": "Pedido obtenido exitosamente",
            "model": OrderResponseModel
        },
        400: {
            "description": "ID de pedido inválido",
            "model": ErrorResponseModel
        },
        404: {
            "description": "Pedido no encontrado",
            "model": ErrorResponseModel
        }
    }
)
async def get_order(order_id: str) -> Dict[str, Any]:
    """
    Obtener un pedido por ID
    """
    db = get_database()
    
    if not ObjectId.is_valid(order_id):
        logger.warning(f"ID de pedido inválido: {order_id}")
        raise BadRequestException("ID de pedido inválido")
    
    try:

        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        
        if not order:
            logger.warning(f"Pedido no encontrado: {order_id}")
            raise NotFoundException("Pedido", order_id)
        
        # Convertir ObjectId a string y datetime a ISO format
        order["_id"] = str(order["_id"])
        if "created_at" in order:
            order["created_at"] = order["created_at"].isoformat()
        
        logger.info(f"Pedido obtenido: {order_id}")
        
        return success_response(
            data=order,
            message="Pedido obtenido exitosamente"
        )
    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        logger.error(f"Error obteniendo pedido {order_id}: {e}")
        raise InternalServerException("Error al obtener el pedido")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderCreateResponseModel,
    responses={
        201: {
            "description": "Pedido creado exitosamente",
            "model": OrderCreateResponseModel
        },
        422: {
            "description": "Errores de validación",
            "model": ErrorResponseModel
        },
        500: {
            "description": "Error interno del servidor",
            "model": ErrorResponseModel
        }
    }
)
async def create_order(order: OrderCreate) -> Dict[str, Any]:
    """
    Crear un nuevo pedido
    **Mensajería**: Publica evento a RabbitMQ para notificaciones
    """
    db = get_database()
    
    try:
        # Preparar documento para MongoDB
        order_dict = order.model_dump()
        order_dict["status"] = "pending"
        order_dict["created_at"] = datetime.now()
        
        # Insertar en MongoDB
        result = await db.orders.insert_one(order_dict)
        order_id = str(result.inserted_id)
        
        logger.info(f"Pedido creado en MongoDB: {order_id}")
        
        # Publicar evento a RabbitMQ
        event_data = {
            "order_id": order_id,
            "customer_id": order.customer_id,
            "total_amount": order.total_amount,
            "products": order.products,
            "timestamp": order_dict["created_at"].isoformat()
        }
        
        publish_success = publish_order_event(event_data)
        
        if not publish_success:
            logger.warning(f"Pedido creado pero no se pudo publicar evento: {order_id}")
        
        # Preparar respuesta
        order_dict["_id"] = order_id
        order_dict["created_at"] = order_dict["created_at"].isoformat()
        
        return success_response(
            data=order_dict,
            message="Pedido creado exitosamente",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Error creando pedido: {e}")
        raise InternalServerException(f"Error al crear el pedido: {str(e)}")
