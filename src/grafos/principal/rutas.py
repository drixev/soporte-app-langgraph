

from typing import Literal

from langgraph.types import Send

from src.constants.enums import Intencion
from src.constants.nodos import NodesName
from src.grafos.principal.estado import Estado


def enrutar(estado: Estado) -> Literal[NodesName.PEDIDOS, NodesName.DEVOLUCIONES, NodesName.RESPONDER]:
    
    if estado["intencion"] == Intencion.PEDIDOS and len(estado["pedido_ids"]) > 1:
        # Fan-out: un Send por pedido; todos corren en paralelo
        return [Send(NodesName.CONSULTAR_UNO, {"pedido_id": pid}) for pid in estado["pedido_ids"]]
    
    if estado["intencion"] == Intencion.FAQ:
        return NodesName.RESPONDER
    return estado["intencion"]
    