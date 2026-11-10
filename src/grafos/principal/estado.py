from typing import Annotated, TypedDict

from langgraph.graph import add_messages

from src.grafos import reducers

class Estado(TypedDict):
    messages: Annotated[list, add_messages]
    intencion: str
    pedido_ids: list[str]
    resultados: Annotated[list, reducers]
    
class EstadoConsulta(TypedDict):
    pedido_id: str