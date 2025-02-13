# models/llm_node.py
from models.nodes import FlowNode
from tkinter import Toplevel, ttk
import re
from models.ollama_client import OllamaClient

class LLMNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "llm", "LLM", "LLM")
        self.config["model"] = {"type": "free", "value": ""}
        self.config["personality"] = {"type": "free", "value": ""}
        self.config["instructions"] = {"type": "free", "value": ""}
        self.config["context"] = {"type": "free", "value": ""}
        self.config["prompt"] = {"type": "free", "value": ""}
        self.config["variable_name"] = ""

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.title("Configurar Nodo LLM")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        entry_title.insert(0, self.title)

        lbl_model = ttk.Label(dialog, text="Modelo:")
        lbl_model.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entry_model = ttk.Entry(dialog, width=40)
        entry_model.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        entry_model.insert(0, self.config["model"]["value"])

        lbl_personality = ttk.Label(dialog, text="Personalidad:")
        lbl_personality.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_personality = ttk.Entry(dialog, width=40)
        entry_personality.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        entry_personality.insert(0, self.config["personality"]["value"])

        lbl_instructions = ttk.Label(dialog, text="Instrucciones:")
        lbl_instructions.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_instructions = ttk.Entry(dialog, width=40)
        entry_instructions.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        entry_instructions.insert(0, self.config["instructions"]["value"])

        lbl_context = ttk.Label(dialog, text="Contexto:")
        lbl_context.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_context = ttk.Entry(dialog, width=40)
        entry_context.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        entry_context.insert(0, self.config["context"]["value"])

        lbl_prompt = ttk.Label(dialog, text="Prompt:")
        lbl_prompt.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        entry_prompt = ttk.Entry(dialog, width=40)
        entry_prompt.grid(row=5, column=1, padx=10, pady=5, sticky="w")
        entry_prompt.insert(0, self.config["prompt"]["value"])

        lbl_var = ttk.Label(dialog, text="Variable de salida:")
        lbl_var.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        entry_var = ttk.Entry(dialog, width=40)
        entry_var.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        entry_var.insert(0, self.config.get("variable_name", ""))

        def on_ok():
            self.title = entry_title.get().strip()
            self.config["model"]["value"] = entry_model.get().strip()
            self.config["personality"]["value"] = entry_personality.get().strip()
            self.config["instructions"]["value"] = entry_instructions.get().strip()
            self.config["context"]["value"] = entry_context.get().strip()
            self.config["prompt"]["value"] = entry_prompt.get().strip()
            self.config["variable_name"] = entry_var.get().strip()
            self.text = f"LLM: {self.config.get('variable_name', '')}" or "LLM"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=7, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=7, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        def resolve_field(cfg):
            if cfg.get("type") == "variable":
                return context.get(cfg.get("value"), "")
            else:
                return cfg.get("value", "")
        model = resolve_field(self.config.get("model", {"type": "free", "value": ""}))
        personality = resolve_field(self.config.get("personality", {"type": "free", "value": ""}))
        instructions = resolve_field(self.config.get("instructions", {"type": "free", "value": ""}))
        context_str = resolve_field(self.config.get("context", {"type": "free", "value": ""}))
        prompt = resolve_field(self.config.get("prompt", {"type": "free", "value": ""}))
        possibles = re.findall(r'\$\{([^}]+)\}', prompt)
        for var in possibles:
            prompt = prompt.replace(f"${{{var}}}", str(context.get(var, "")))
        message = {
            "personality": personality,
            "instructions": instructions,
            "context": context_str,
            "prompt": prompt
        }
        client = OllamaClient(model)
        answer = client.chat(message)
        var_name = self.config.get("variable_name", "respuesta")
        context[var_name] = answer
        print(f"LLM: {prompt} | Respuesta: {answer}")
        return self.connected_to
