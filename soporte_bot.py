from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

llm = init_chat_model("gpt-4o-mini", model_provider="openia", temperature=0)

SYSTEM="Eres el asistente de soporte de TiendaNova. Responde breve y amable."

# memory
class Estado(TypedDict):
    messages: Annotated[list, add_messages]
    
# model
class Clasificacion(BaseModel):
    intencion: Literal["pedidos","devoluciones","faq"] = Field(description="Qué necesita el cliente")
    

clasificador = llm.with_structured_output(Clasificacion)

# nodes
def responder(estado: Estado):
    respuesta = llm.invoke([("system", SYSTEM), *estado["messages"]])
    return { "messages": [respuesta] }

def clasificar(estado: Estado):
    resultado = clasificador.invoke([
        ("system","Clasifica el último mensaje del cliente"),
        *estado["messages"]
    ])
    
    return {"intencion", resultado.intencion}

def pedidos(estado: Estado):
    instrucciones = SYSTEM + " Ayudas con el estado de pedidos."
    respuesta = llm.invoke([("system", instrucciones), *estado["messages"]])
    return {"messages":[respuesta]}

def devoluciones(estado: Estado):
    instrucciones = SYSTEM + " Gestionas devoluciones."
    respuesta = llm.invoke([("system", instrucciones), *estado["messages"]])
    return {"messages", [respuesta]}

# Routes
def enrutar(estado: Estado) -> Literal["pedidos","devoluciones", "responder"]:
    if estado["intencion"] == "faq":
        return "responder"
    return estado["intencion"]
    

# graph building
builder = StateGraph(Estado)
builder.add_node("clasificar", clasificar)
builder.add_node("pedidos", pedidos)
builder.add_node("devoluciones", devoluciones)
builder.add_node("responder", responder)

# edges
builder.add_edge(START, "clasificar")
builder.add_conditional_edges("clasificar", enrutar)
builder.add_edge("pedidos", END)
builder.add_edge("devoluciones", END)
builder.add_edge("responder", END)

# build
grafo = builder.compile()

# Test
if __name__ == "main":
    print(grafo.get_graph().draw_mermaid()) # dibuja el grafo
    salida = grafo.invoke({"messages": [("user", "Quiero devolver mi teclado")]})
    print(salida["intencion"], "->", salida["messages"][-1].content)

 