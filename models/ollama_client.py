# models/ollama_client.py
try:
    from ollama import chat
    from ollama import ChatResponse
except ImportError:
    raise ImportError("La librería oficial de Ollama no está instalada.")

class OllamaClient:
    def __init__(self, model):
        self.model = model

    def chat(self, message):
        messages = [
            {'role': 'system', 'content': message["personality"]},
            {'role': 'system', 'content': message["instructions"]},
        ]
        if message["context"]:
            messages.append({'role': 'system', 'content': message["context"]})
        messages.append({'role': 'user', 'content': message["prompt"]})
        response: ChatResponse = chat(model=self.model, messages=messages)
        return response['message']['content']