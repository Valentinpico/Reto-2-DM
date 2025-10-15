from typing import Any, Optional, Union, List, Dict
from pydantic import BaseModel


class StandardResponse(BaseModel):
    """Modelo de respuesta estandarizado"""
    success: bool
    statusCode: int
    message: str
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]], Dict]] = None
    count: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "statusCode": 200,
                "message": "Operación exitosa",
                "data": {},
                "count": 1
            }
        }


def success_response(
    data: Optional[Union[Dict, List[Dict], Any]] = None,
    message: str = "Operación exitosa",
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Crear respuesta exitosa estandarizada
    """
    response = {
        "success": True,
        "statusCode": status_code,
        "message": message
    }
    
    if data is not None:

        if isinstance(data, list):
            response["count"] = len(data)
        response["data"] = data
    
    return response


def error_response(
    message: str = "Error en la operación",
    status_code: int = 400,
    data: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Crear respuesta de error estandarizada
    """
    response = {
        "success": False,
        "statusCode": status_code,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return response
