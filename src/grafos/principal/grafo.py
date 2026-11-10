from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.store.memory import InMemoryStore

from src.contexto import Contexto
from src.grafos.principal.estado import Estado
from src.grafos.principal.rutas import enrutar
from src.herramientas import HERRAMIENTAS
from src.constants.nodos import NodesName
from src.grafos.principal.nodos import clasificar, pedidos, responder, consultar_uno, resumir
from src.grafos.devolucion import contruir_subgrafo

# grafo
checkpointer = InMemorySaver(); # memory per thread (thread_id)
store = InMemoryStore();        # memory entre hilos (por cliente) 

def agregar_nodos(builder: StateGraph, subgrafo)-> None:
    builder.add_node(NodesName.CLASIFICAR, clasificar)
    builder.add_node(NodesName.PEDIDOS, pedidos)
    builder.add_node(NodesName.DEVOLUCIONES, subgrafo) # un grafo compilado como otro nodo
    builder.add_node(NodesName.RESPONDER, responder)
    builder.add_node(NodesName.TOOLS, ToolNode(HERRAMIENTAS))
    builder.add_node(NodesName.CONSULTAR_UNO, consultar_uno)
    builder.add_node(NodesName.RESUMIR, resumir)
    
def agregar_edges(builder:StateGraph)->None:
    builder.add_edge(START, NodesName.CLASIFICAR)
    builder.add_conditional_edges(
        NodesName.CLASIFICAR, enrutar, [
            NodesName.PEDIDOS, 
            NodesName.DEVOLUCIONES, 
            NodesName.RESPONDER, 
            NodesName.CONSULTAR_UNO
            ]
    )
    builder.add_conditional_edges(NodesName.PEDIDOS, tools_condition)   # ¿pidió una tool? -> "Tools" o END
    builder.add_edge(NodesName.TOOLS, NodesName.PEDIDOS)                # el resultado vuelve al LLM 
    builder.add_edge(NodesName.DEVOLUCIONES, END)
    builder.add_edge(NodesName.RESPONDER, END)
    builder.add_edge(NodesName.CONSULTAR_UNO, NodesName.RESUMIR)
    builder.add_edge(NodesName.RESUMIR, END)


def construir_grafo():
    subgrafo = contruir_subgrafo()
    
    builder = StateGraph(Estado, context_schema=Contexto)
    agregar_nodos(builder, subgrafo)
    agregar_edges(builder)
    
    return builder.compile(checkpointer=checkpointer, store=store)