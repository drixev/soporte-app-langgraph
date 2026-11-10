from langgraph.runtime import Runtime

from src.contexto import Contexto

def notas_cliente(runtime: Runtime[Contexto]) -> list[str]: 
    """Lee la memoria a largo plazo de cliente (compartida entre hilos)"""
    espacio = ("clientes", runtime.context["cliente_id"])
    return [item.value["texto"] for item in runtime.store.search(espacio)]
