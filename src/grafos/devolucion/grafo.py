from langgraph.graph import END, START, StateGraph

from src.constants.nodos import NodesName
from src.contexto import Contexto
from src.grafos.devolucion.estado import EstadoDevolucion
from src.grafos.devolucion.nodos import aprobacion, confirmar, validar
from src.grafos.devolucion.rutas import tras_validar

def agregar_nodos(sub:StateGraph) -> None:
    sub.add_node(NodesName.VALIDAR, validar)
    sub.add_node(NodesName.APROBACION, aprobacion)
    sub.add_node(NodesName.CONFIRMAR,confirmar)    
    
def agregar_edges(sub:StateGraph) -> None:
    sub.add_edge(START, NodesName.VALIDAR)
    sub.add_conditional_edges(NodesName.VALIDAR, tras_validar)
    sub.add_edge(NodesName.APROBACION, NodesName.CONFIRMAR)
    sub.add_edge(NodesName.CONFIRMAR, END)
    
def contruir_subgrafo():
    sub = StateGraph(EstadoDevolucion, context_schema=Contexto)
    agregar_nodos(sub)
    agregar_edges(sub);
    return sub.compile()
    
