# models/inicio_node.py
from models.nodes import FlowNode
from tkinter import Toplevel, ttk

class InicioNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "inicio", "Inicio", "Inicio")
    
    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.title("Configurar Nodo Inicio")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        entry_title.insert(0, self.title)
        
        def on_ok():
            self.title = entry_title.get().strip()
            self.text = self.title
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=1, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=1, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        # El nodo de inicio simplemente retorna el siguiente nodo
        return self.connected_to
