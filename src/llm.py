from langchain.chat_models import init_chat_model

from src.config import MODELO
from src.schemas.clasificacion import Clasificacion
from src.herramientas.tienda import buscar_producto, consultar_pedido

llm = init_chat_model(MODELO, temperature=0)

clasificador = llm.with_structured_output(Clasificacion)

herramientas = [consultar_pedido, buscar_producto]

llm_con_tools = llm.bind_tools(herramientas)