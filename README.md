# Bot de soporte con LangGraph

Proyecto de práctica: un asistente de atención al cliente para una tienda, construido con [LangGraph](https://langchain-ai.github.io/langgraph/).

## Qué hace

El bot clasifica cada mensaje del cliente y lo dirige al flujo adecuado:

- **Pedidos**: consulta el estado de un pedido o busca productos usando herramientas (tools).
- **Varios pedidos a la vez**: los consulta en paralelo y devuelve un resumen.
- **Devoluciones**: un sub-grafo que valida el pedido y pide **aprobación humana** (human in the loop) antes de confirmar el reembolso.
- **Preguntas generales**: responde directamente con el LLM.

Además tiene dos tipos de memoria:

- **Por conversación** (`thread_id`): recuerda el historial del hilo.
- **Por cliente** (`cliente_id`): guarda preferencias que se mantienen entre conversaciones (por ejemplo, preferir crédito de tienda en las devoluciones).

Los datos de pedidos y catálogo son de prueba (`src/datos/mock.py`).

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.template .env           # y completa la variable MODELO (y la API key si aplica)
```

El modelo se elige en `.env` con el formato `proveedor:modelo`. Por defecto usa `ollama:llama3.1:8b` (local, sin API key); también funciona con Anthropic, OpenAI o Google.

Para comprobar que el modelo responde:

```bash
python scripts/probar_modelo.py
```

## Uso

```bash
python -m src.app
```

Ejecuta una demo que muestra el grafo en formato Mermaid y simula dos conversaciones del mismo cliente para mostrar la memoria entre hilos.

## Estructura

```
src/
├── app.py            # punto de entrada / demo
├── config.py         # lectura del .env
├── llm.py            # modelos configurados
├── memoria.py        # memoria a largo plazo del cliente
├── grafos/
│   ├── principal/    # grafo principal (clasificar, pedidos, responder...)
│   └── devolucion/   # sub-grafo de devoluciones
├── herramientas/     # tools que puede usar el LLM
├── prompts/          # prompts del sistema
└── datos/            # datos de prueba
```
