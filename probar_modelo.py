import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
modelo = os.getenv("MODELO")
llm = init_chat_model(modelo, temperature=0)
print(modelo, "->", llm.invoke("Responde solo con la palabra: listo").content)
