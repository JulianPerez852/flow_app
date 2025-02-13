# models/accion_node.py
from models.nodes import FlowNode
from tkinter import Toplevel, ttk, simpledialog

class AccionNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "accion", "Acción", "Acción")
        self.config["action_type"] = "imprimir"  # Valor por defecto

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()

        dialog.title("Configurar Nodo de Acción")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        entry_title.insert(0, self.title)

        lbl_action = ttk.Label(dialog, text="Tipo de Acción:")
        lbl_action.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        action_var = ttk.Combobox(dialog, values=["imprimir", "pregunta"], state="readonly")
        action_var.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        action_var.set(self.config.get("action_type", "imprimir"))

        lbl_message = ttk.Label(dialog, text="Mensaje/Texto:")
        lbl_message.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_message = ttk.Entry(dialog, width=40)
        entry_message.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        entry_message.insert(0, self.config.get("print_text", ""))

        lbl_question = ttk.Label(dialog, text="Pregunta:")
        lbl_question.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_question = ttk.Entry(dialog, width=40)
        entry_question.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        entry_question.insert(0, self.config.get("question", ""))

        lbl_var = ttk.Label(dialog, text="Variable (para almacenar respuesta):")
        lbl_var.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_var = ttk.Entry(dialog, width=40)
        entry_var.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        entry_var.insert(0, self.config.get("variable_name", ""))

        def on_ok():
            self.title = entry_title.get().strip()
            act_type = action_var.get().strip()
            self.config["action_type"] = act_type
            if act_type == "imprimir":
                text = entry_message.get().strip()
                self.config["print_text"] = text
                self.text = text
            else:
                q = entry_question.get().strip()
                var_name = entry_var.get().strip()
                self.config["question"] = q
                self.config["variable_name"] = var_name
                self.text = f"? {var_name}"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=5, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=5, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        act_type = self.config.get("action_type", "imprimir")
        if act_type == "imprimir":
            message = self.config.get("print_text", self.text)
            print(f"Acción imprimir: {message}")
        else:
            question = self.config.get("question", "Ingrese respuesta:")
            var_name = self.config.get("variable_name", "respuesta")
            # Se asume que 'context' incluye la raíz para diálogos
            root = context.get("root")
            answer = simpledialog.askstring("Pregunta", question, parent=root)
            print(f"Pregunta: {question} | Respuesta: {answer}")
            context[var_name] = answer
        return self.connected_to
