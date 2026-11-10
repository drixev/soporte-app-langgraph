from enum import StrEnum

class NodesName(StrEnum):
    CLASIFICAR = "clasificar"
    PEDIDOS = "pedidos"
    DEVOLUCIONES = "devoluciones"
    RESPONDER = "responder"
    TOOLS = "tools"
    CONSULTAR_UNO = "consultar_uno"
    VALIDAR = "validar"
    APROBACION = "aprobacion"
    CONFIRMAR = "confirmar"
    RESUMIR = "resumir"
    END = "__end__"