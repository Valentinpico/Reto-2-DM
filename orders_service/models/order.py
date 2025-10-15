from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom type for MongoDB ObjectId"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, handler):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class OrderCreate(BaseModel):
    """Modelo para crear un pedido"""
    customer_id: str = Field(..., description="ID del cliente")
    products: List[str] = Field(..., min_length=1, description="Lista de productos (mínimo 1)")
    total_amount: float = Field(..., gt=0, description="Monto total del pedido")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_id": "customer_123",
                "products": ["Laptop Dell XPS 15", "Mouse Logitech MX Master", "Teclado mecánico"],
                "total_amount": 1499.97
            }
        }
    )


class OrderResponse(BaseModel):
    """Modelo de respuesta de pedido"""
    id: str = Field(alias="_id", description="ID del pedido")
    customer_id: str
    products: List[str]
    total_amount: float
    status: str
    created_at: datetime
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class OrderInDB(BaseModel):
    """Modelo de pedido en la base de datos"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    customer_id: str
    products: List[str]
    total_amount: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
