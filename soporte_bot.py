import os
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

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

# memory
class Estado(TypedDict):
    messages: Annotated[list, add_messages]
    intencion: str
    
# model
class Clasificacion(BaseModel):
    intencion: Literal["pedidos","devoluciones","faq"] = Field(description="Qué necesita el cliente")
    
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
    respuesta = llm.invoke([("system", SYSTEM), *estado["messages"]])
    return { "messages": [respuesta] }

def clasificar(estado: Estado):
    resultado = clasificador.invoke(
        [("system","Clasifica el último mensaje del cliente"), *estado["messages"]]
    )
    
    return {"intencion": resultado.intencion}

def pedidos(estado: Estado):
    instrucciones = SYSTEM + " Ayudas con el estado de pedidos."
    respuesta = llm_con_tools.invoke([("system", instrucciones), *estado["messages"]])
    # respuesta = llm.invoke([("system", instrucciones), *estado["messages"]])
    return {"messages":[respuesta]}

def devoluciones(estado: Estado):
    instrucciones = SYSTEM + " Gestionas devoluciones."
    respuesta = llm.invoke([("system", instrucciones), *estado["messages"]])
    return {"messages", [respuesta]}

# Routes
def enrutar(estado: Estado) -> Literal["pedidos","devoluciones", "responder"]:
    print("data",estado)
    if estado["intencion"] == "faq":
        return "responder"
    return estado["intencion"]
    

# graph building
builder = StateGraph(Estado)
builder.add_node("clasificar", clasificar)
builder.add_node("pedidos", pedidos)
builder.add_node("devoluciones", devoluciones)
builder.add_node("responder", responder)
builder.add_node("tools", ToolNode(herramientas))

# edges
builder.add_edge(START, "clasificar")
builder.add_conditional_edges("clasificar", enrutar)
builder.add_conditional_edges("pedidos", tools_condition)   # ¿pidió una tool? -> "Tools" o END
builder.add_edge("tools", "pedidos")                        # el resultado vuelve al LLM 
builder.add_edge("devoluciones", END)
builder.add_edge("responder", END)

# build
grafo = builder.compile()

# Test
if __name__ == "__main__":
    print(grafo.get_graph().draw_mermaid()) # dibuja el grafo
    salida = grafo.invoke({"messages": [("user", "¿Dónde está mi pedido 123?")]})
    #print(salida["intencion"], "->", salida["messages"][-1].content)
    for m in salida["messages"]:
        m.pretty_print()

 