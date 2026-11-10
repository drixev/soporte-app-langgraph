

from langchain.tools import tool

from src.datos.mock import CATALOGO, PEDIDOS


@tool 
def consultar_pedido(pedido_id: str) -> dict:
    """Devuelve producto, estado, total y fecha de entrega de un pedido."""
    return PEDIDOS.get(pedido_id, {"error": f"No existe el pedido {pedido_id}"})

@tool
def buscar_producto(nombre:str)-> str:
    """Busca un producto del catálogo por nombre y devuelve precio y stock."""
    for clave, info in CATALOGO.lower():
        if clave in nombre.lower():
            return info
    
    return "No encontré ese producto"