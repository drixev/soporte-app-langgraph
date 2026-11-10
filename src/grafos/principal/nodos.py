from uuid import uuid4

from langchain.messages import AIMessage
from langgraph.runtime import Runtime

from src.llm import llm, clasificador, llm_con_tools

from src.constants.enums import Role
from src.contexto import Contexto
from src.datos.mock import PEDIDOS
from src.grafos.principal.estado import Estado, EstadoConsulta
from src.memoria import notas_cliente
from src.prompts.soporte import SYSTEM_PROMPT


def responder(estado: Estado, runtime: Runtime[Contexto]):
    sistema = SYSTEM_PROMPT + " Notas del cliente: "+"; ".join(notas_cliente(runtime))
    respuesta = llm.invoke([(Role.SYSTEM, sistema), *estado["messages"]])
    
    return { "messages": [respuesta] }

def clasificar(estado: Estado, runtime: Runtime[Contexto]):
    resultado = clasificador.invoke(
        [(Role.SYSTEM,"Clasifica el último mensaje del cliente"), *estado["messages"]]
    )
    
    if resultado.preferencia:
        espacio = ("clientes", runtime.context["cliente_id"])
        runtime.store.put(espacio, str(uuid4()), {"texto": resultado.preferencia})
    
    return {
        "intencion": resultado.intencion, 
        "pedido_ids": resultado.pedido_ids,
        "resultados": None # Reinicia los resultados del turno anterior
    }

def pedidos(estado: Estado, runtime: Runtime[Contexto]):
    instrucciones = SYSTEM_PROMPT + " Ayudas con el estado de pedidos."
    instrucciones += " Notas del cliente: "+ "; ".join(notas_cliente(runtime))
    respuesta = llm_con_tools.invoke([(Role.SYSTEM, instrucciones), *estado["messages"]])
    return {"messages":[respuesta]}
    
def consultar_uno(estado: EstadoConsulta):
    """Se ejecuta una vez por pedido, en paralelo, gracias a Send"""
    pedido = PEDIDOS.get(estado["pedido_id"], {"producto":"?", "estado":"no encontrado"})
    return {"resultados": [{"id": estado["pedido_id"], **pedido}]}

def resumir(estado: Estado):
    lineas = [
        f"- Pedido {r['id']}: {r['producto']} - {r['estado']}" 
        for r in sorted(estado["resultados"], key=lambda r: r["id"])
    ]
    return {"messages": [AIMessage("Esto encontré: \n" +"\n".join(lineas))]}
    