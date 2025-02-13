# models/ollama_client.py
try:
    from ollama import chat
    from ollama import ChatResponse  # Se asume que la librería oficial se llama "ollama"
except ImportError:
    raise ImportError("La librería oficial de Ollama no está instalada.")
class OllamaClient:
    def __init__(self, model):
        # Importar la librería oficial de Ollama
        print(model)
        self.model = model
    
    def chat(self, message):
        # Llama al método oficial para enviar el prompt y obtener la respuesta.

        messages = [
            {
                'role': 'system',
                'content': message["personality"],
            },
            {
                'role': 'system',
                'content': message["instructions"],
            },
        ]

        if message["context"]:
            context_str = str(message["context"]) if not isinstance(message["context"], str) else message["context"]
            messages.append({
                'role': 'system',
                'content': context_str,
            })

        messages.append({
            'role': 'user',
            'content': message["prompt"],
        })

        response: ChatResponse = chat(
            model=self.model, 
            messages=messages
            )
        return response['message']['content']
