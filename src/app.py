from src.constants.nodos import NodesName

from src.grafos.principal import grafo


# Test
if __name__ == "__main__":
    print(grafo.get_graph().draw_mermaid()) # dibuja el grafo
    
    contexto = {"cliente_id": "42"}
    
    config_a = {"configurable": {"thread_id": "A"}}
    entrada = {"messages":[("user", "Para devoluciones prefiero crédito de tienda")]}
    
    # Hilo A: el cliente expresa su preferencia -> se guarda en el store
    grafo.invoke(entrada,config=config_a,context=contexto)
    
    # Hilo B (conversación nueva): la preferencia sigue disponiblke
    config_b= {"configurable": {"thread_id": "B"}} 
    entrada = {"messages": [("user", "Quiero devolver el pedido 456")]}

    for modo, dato in grafo.stream(
        entrada, config_b, context=contexto, stream_mode=["updates", "messages"]
    ):
        if modo == "updates":
            print(f"[{', '.join(dato)}] terminó")
        else:
            chunk, meta = dato
            if meta["langgraph_node"] in (NodesName.RESPONDER, NodesName.PEDIDOS):
                print(chunk.text, end="",flush=True)
            
        
    print(grafo.get_state(config_b).values["messages"][-1].content)
 