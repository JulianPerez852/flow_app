# models/multiples_node.py
from models.nodes import FlowNode
from tkinter import Toplevel, ttk, simpledialog

class MultiplesNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "multiples", "Múltiples Respuestas", "Pregunta Múltiple")
        self.config["question"] = ""
        self.config["responses"] = []
        self.config["variable_name"] = ""

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.title("Configurar Nodo Múltiples Respuestas")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        entry_title.insert(0, self.title)

        lbl_question = ttk.Label(dialog, text="Pregunta:")
        lbl_question.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entry_question = ttk.Entry(dialog, width=40)
        entry_question.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        entry_question.insert(0, self.config.get("question", ""))

        lbl_responses = ttk.Label(dialog, text="Respuestas (separadas por coma):")
        lbl_responses.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_responses = ttk.Entry(dialog, width=40)
        entry_responses.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        entry_responses.insert(0, ",".join(self.config.get("responses", [])))

        lbl_var = ttk.Label(dialog, text="Variable (para almacenar respuesta):")
        lbl_var.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_var = ttk.Entry(dialog, width=40)
        entry_var.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        entry_var.insert(0, self.config.get("variable_name", ""))

        def on_ok():
            self.title = entry_title.get().strip()
            self.config["question"] = entry_question.get().strip()
            responses = [r.strip() for r in entry_responses.get().split(",") if r.strip()]
            self.config["responses"] = responses
            self.config["variable_name"] = entry_var.get().strip()
            self.text = f"? {self.config['variable_name']}" if self.config["variable_name"] else "Múltiples"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=4, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=4, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        question = self.config.get("question", "Seleccione una opción:")
        responses = self.config.get("responses", [])
        var_name = self.config.get("variable_name", "respuesta")
        root = context.get("root")
        answer = simpledialog.askstring("Pregunta Múltiple", f"{question}\nOpciones: {', '.join(responses)}", parent=root)
        print(f"Múltiples: {question} | Respuesta: {answer}")
        context[var_name] = answer
        return self.connected_to
