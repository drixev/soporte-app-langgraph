from typing import Annotated, TypedDict

from langgraph.graph import add_messages

class EstadoDevolucion(TypedDict):
    messages: Annotated[list, add_messages] # compartida con el grafo padre
    pedido_ids: list[str]                   # compartida con el grafo padre
    pedido: dict                            # privada del subgrafo
    aprobada: bool                          # privada del subgrafo
    