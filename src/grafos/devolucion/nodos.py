from langchain.messages import AIMessage
from langgraph.types import interrupt
from langgraph.runtime import Runtime

from src.constants.enums import Accion
from src.contexto import Contexto
from src.datos.mock import PEDIDOS
from src.grafos.devolucion.estado import EstadoDevolucion
from src.memoria import notas_cliente

def validar(estado: EstadoDevolucion):
    ids = estado["pedido_ids"]
    if not ids or ids[0] not in PEDIDOS:
        return { "pedido":{}, "messages": [AIMessage("¿Me confirmas el número de pedido a devolver?")] }
    return {"pedido": { "id": ids[0], **PEDIDOS[ids[0]] }, "aprobada": True}

def aprobacion(estado:EstadoDevolucion):
    p = estado["pedido"]
    decision = interrupt({"accion":"aprobar_devolucion", "pedido":p["id"], "monto":p["total"]})
    return {"aprobada": decision == Accion.APROBAR}


def confirmar(estado: EstadoDevolucion, runtime: Runtime[Contexto]):
    p = estado["pedido"]
    
    if not estado["aprobada"]:
        return {"messages": [AIMessage(f"La devolución del pedido {p['id']} no fue aprobada.")]}
    
    prefiere_credito = any("crédito" in nota for nota in notas_cliente(runtime))
    metodo = "crédito de tienda" if prefiere_credito else "tu método de pago original"
    
    mensaje  = f"Devolución del pedido {p['id']} registrada. Reembolso de ${p['total']:.2f} como {metodo}."
    return {"messages": [AIMessage(mensaje)]}