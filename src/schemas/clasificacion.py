from typing import Literal

from pydantic import BaseModel, Field

class Clasificacion(BaseModel):
    intencion: Literal["pedidos", "devoluciones", "faq"] = Field(description="Qué necesita el cliente")
    pedido_ids: list[str] = Field(default_factory=list, description="Números de pedidos mencionados")
    preferencia: str | None = Field(default=None, description="Preferencia duradera del cliente, si la expresó")