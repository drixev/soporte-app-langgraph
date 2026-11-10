from typing import Literal

from langgraph.graph import END

from src.constants.nodos import NodesName
from src.grafos.devolucion.estado import EstadoDevolucion

LIMITE_SIN_APROBACION = 100 # devoluciones mayores requieren supervisor

def tras_validar(estado:EstadoDevolucion) -> Literal[NodesName.APROBACION, NodesName.CONFIRMAR, NodesName.END]:
    if not estado["pedido"]:
        return END
    if estado["pedido"]["total"] > LIMITE_SIN_APROBACION:
        return NodesName.APROBACION
    return NodesName.CONFIRMAR