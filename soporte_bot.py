import os
from typing import Annotated, Literal, TypedDict
from enum import StrEnum

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

load_dotenv() # lee las apis keys y el modelo desde el archivo .env

# "proveedor:modelo". Se cambia en el .env sin tocar el código
# MODELO = os.getenv("MODELO", "openia:gpt-4.1-mini")
# MODELO = os.getenv("MODELO", "anthropic:claude-sonnet-5-5")
MODELO = os.getenv("MODELO", "ollama:llama3.1:8b")

llm = init_chat_model(MODELO, temperature=0)

SYSTEM="Eres el asistente de soporte de TiendaNova. Responde breve y amable."

# Datos simulados (en un caso real. tu base de datos o api)
PEDIDOS = {
    "123":{ "producto": "Audífonos Pulse", "estado": "en camino", "total": 59.90, "entrega": "2 nov"},
    "456":{ "producto": "Teclado Arc", "estado": "entregado", "total": 89.00, "entrega": "25 oct"},
    "789":{ "producto": "Monitor Vista 27", "estado": "entregado", "total": 289.00, "entrega": "20 oct" },
}

CATALOGO = {
    "pulse": "Audífonos Pulse: $59.90, 14 en stock",
    "arc": "Teclado Arc: $89.00, 3 en stock",
    "vista": "Monitor Vista 27: $289.00, sin stock"
}

LIMITE_SIN_APROBACION = 100 # devoluciones mayores requieren supervisor

class CamposEstado(StrEnum):
    MENSAGES = "messages"
    INTENCION = "intencion"
    PEDIDO_IDS = "pedido_ids"
    PEDIDO = "pedido"
    APROBADA = "aprobada"

# memory
class Estado(TypedDict):
    messages: Annotated[list, add_messages]
    intencion: str
    pedido_ids: list[str]
    
# model
class Clasificacion(BaseModel):
    intencion: Literal["pedidos","devoluciones","faq"] = Field(description="Qué necesita el cliente")
    pedido_ids: list[str] = Field(default_factory=list, description="Números de pedidos mencionados")
    
clasificador = llm.with_structured_output(Clasificacion)

# tools

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


herramientas = [consultar_pedido, buscar_producto]

llm_con_tools = llm.bind_tools(herramientas)

# nodes

def responder(estado: Estado):
    respuesta = llm.invoke([("system", SYSTEM), *estado[CamposEstado.MENSAGES]])
    return { CamposEstado.MENSAGES: [respuesta] }

def clasificar(estado: Estado):
    resultado = clasificador.invoke(
        [("system","Clasifica el último mensaje del cliente"), *estado[CamposEstado.MENSAGES]]
    )
    
    return {CamposEstado.INTENCION: resultado.intencion, CamposEstado.PEDIDO_IDS: resultado.pedido_ids}

def pedidos(estado: Estado):
    instrucciones = SYSTEM + " Ayudas con el estado de pedidos."
    respuesta = llm_con_tools.invoke([("system", instrucciones), *estado[CamposEstado.MENSAGES]])
    # respuesta = llm.invoke([("system", instrucciones), *estado[CamposEstado.MENSAGES]])
    return {CamposEstado.MENSAGES:[respuesta]}

# subgrafo devoluciones
class EstadoDevolucion(TypedDict):
    messages: Annotated[list, add_messages] # compartida con el grafo padre
    pedido_ids: list[str]                   # compartida con el grafo padre
    pedido: dict                            # privada del subgrafo
    aprobada: bool                          # privada del subgrafo
    
# nodos del subgrafo
def validar(estado: EstadoDevolucion):
    ids = estado[CamposEstado.PEDIDO_IDS]
    if not ids or ids[0] not in PEDIDOS:
        return { CamposEstado.PEDIDO: [AIMessage("¿Me confirmas el número de pedido a devolver?")] }
    return {CamposEstado.PEDIDO: { "id": ids[0], **PEDIDOS[ids[0]] }, CamposEstado.APROBADA: True}
        
def tras_validar(estado:EstadoDevolucion) -> Literal["aprobacion", "confirmar", "__end__"]:
    if not estado[CamposEstado.PEDIDO]:
        return END
    if estado[CamposEstado.PEDIDO]["total"] > LIMITE_SIN_APROBACION:
        return "aprobacion"
    return "confirmar"

def aprobacion(estado:EstadoDevolucion):
    p = estado[CamposEstado.PEDIDO]
    decision = interrupt({"accion":"aprobar_devolucion", "pedido":p["id"], "monto":p["total"]})
    return {CamposEstado.APROBADA: decision == "aprobar"}


def confirmar(estado: EstadoDevolucion):
    p = estado[CamposEstado.PEDIDO]
    
    if not estado[CamposEstado.APROBADA]:
        return {CamposEstado.MENSAGES: [AIMessage(f"La devolución del pedido {p['id']} no fue aprobada.")]}
    
    mensaje  = f"Devolución del pedido {p['id']} registrada. Reembolso de ${p['total']:.2f} en 3-5 dias."
    return {CamposEstado.MENSAGES: [AIMessage(mensaje)]}

sub = StateGraph(EstadoDevolucion)
sub.add_node("validar", validar)
sub.add_node("aprobacion", aprobacion)
sub.add_node("confirmar",confirmar)

sub.add_edge(START, "validar")
sub.add_conditional_edges("validar", tras_validar)
sub.add_edge("aprobacion", "confirmar")
sub.add_edge("confirmar", END)

subgrafo_devoluciones = sub.compile()

# Routes
def enrutar(estado: Estado) -> Literal["pedidos","devoluciones", "responder"]:
    if estado[CamposEstado.INTENCION] == "faq":
        return "responder"
    return estado[CamposEstado.INTENCION]
    

# graph building
builder = StateGraph(Estado)
builder.add_node("clasificar", clasificar)
builder.add_node("pedidos", pedidos)
builder.add_node("devoluciones", subgrafo_devoluciones) # un grafo compilado como otro nodo
builder.add_node("responder", responder)
builder.add_node("tools", ToolNode(herramientas))

# edges
builder.add_edge(START, "clasificar")
builder.add_conditional_edges("clasificar", enrutar)
builder.add_conditional_edges("pedidos", tools_condition)   # ¿pidió una tool? -> "Tools" o END
builder.add_edge("tools", "pedidos")                        # el resultado vuelve al LLM 
builder.add_edge("devoluciones", END)
builder.add_edge("responder", END)

# memory per thread
checkpointer = InMemorySaver();

# build
grafo = builder.compile(checkpointer=checkpointer)

# Test
if __name__ == "__main__":
    print(grafo.get_graph().draw_mermaid()) # dibuja el grafo
    
    # config = {"configurable": { "thread_id" : "client" }}
    # grafo.invoke({CamposEstado.MENSAGES: [("user", "¿Dónde está mi pedido 123?")]}, config)
    # salida = grafo.invoke({CamposEstado.MENSAGES: [("user", "¿Y cuanto pagué?")]}, config)
    # print(salida["intencion"], "->", salida[CamposEstado.MENSAGES][-1].content)
    # estado = grafo.get_state(config)
    # print("Mensajes guardados en el hilo", len(estado.values[CamposEstado.MENSAGES]))
    # for m in salida[CamposEstado.MENSAGES]:
    #     m.pretty_print()
    
    config = {"configurable":{"thread_id": "client-77"}}
    salida = grafo.invoke({"messages": [("user", "¿Quier deolver el pedido 789?")]}, config)
    print("Pausado:", salida["__interrupt__"][0].value)
    print("Siguiente nodo:", grafo.get_state(config).next)
    salida = grafo.invoke(Command(resume="aprobar"), config) # el supervisor aprueba
    
    for m in salida[CamposEstado.MENSAGES]:
        m.pretty_print()

 