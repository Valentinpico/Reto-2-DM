from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    """Modelo de respuesta estandarizado"""
    success: bool
    statusCode: int
    message: str
    data: Optional[Any] = None
    count: Optional[int] = None


class HealthResponseModel(StandardResponse):
    """Respuesta del health check"""
    data: Dict[str, str] = Field(
        default={"status": "healthy", "service": "Orders Service"}
    )


class OrderResponseModel(StandardResponse):
    """Respuesta de orden única"""
    data: Dict[str, Any] = Field(
        default={
            "_id": "507f1f77bcf86cd799439011",
            "customer_id": "customer_123",
            "products": ["Laptop", "Mouse", "Teclado"],
            "total_amount": 99.99,
            "status": "pending",
            "created_at": "2024-01-01T10:30:00"
        }
    )


class OrderListResponseModel(StandardResponse):
    """Respuesta de lista de órdenes"""
    data: List[Dict[str, Any]] = Field(default=[])
    count: int = Field(default=0)


class OrderCreateResponseModel(StandardResponse):
    """Respuesta de creación de orden"""
    statusCode: int = Field(default=201)
    data: Dict[str, Any] = Field(
        default={
            "_id": "507f1f77bcf86cd799439011",
            "customer_id": "customer_123",
            "products": ["Laptop", "Mouse", "Teclado"],
            "total_amount": 99.99,
            "status": "pending",
            "created_at": "2024-01-01T10:30:00"
        }
    )


class ErrorResponseModel(StandardResponse):
    """Respuesta de error"""
    success: bool = Field(default=False)
    data: Optional[Dict[str, Any]] = None
