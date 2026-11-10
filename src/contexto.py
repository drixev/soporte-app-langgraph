from typing import TypedDict

# Contexto de ejecución (NO es estado: no cambia durante la ejecución)
class Contexto(TypedDict):
    cliente_id: str