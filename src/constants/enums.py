from enum import StrEnum

class Accion(StrEnum):
    APROBAR = "aprobar"

class Intencion(StrEnum):
    PEDIDOS= "pedidos"
    DEVOLUCIONES = "devoluciones"
    FAQ = "faq"
    
class Role(StrEnum):
    SYSTEM="system"
    USER="user"