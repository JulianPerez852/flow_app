# models/python_node.py
from models.nodes import FlowNode
from tkinter import Toplevel, ttk, messagebox, simpledialog
import traceback

class PythonNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "python", "Python", "Ejecutar Código Python")
        self.config["code"] = ""
        self.config["params"] = []
        self.config["variable_name"] = ""

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.title("Configurar Nodo Python")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=50)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        entry_title.insert(0, self.title)

        lbl_code = ttk.Label(dialog, text="Código (defina una función 'func'):")
        lbl_code.grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        txt_code = dialog.tk.Text(dialog, width=60, height=10)
        txt_code.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        txt_code.insert("1.0", self.config.get("code", ""))

        lbl_params = ttk.Label(dialog, text="Parámetros (coma-separados):")
        lbl_params.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_params = ttk.Entry(dialog, width=50)
        entry_params.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        entry_params.insert(0, ", ".join(self.config.get("params", [])))

        lbl_var = ttk.Label(dialog, text="Variable de salida:")
        lbl_var.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_var = ttk.Entry(dialog, width=50)
        entry_var.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        entry_var.insert(0, self.config.get("variable_name", ""))

        def on_ok():
            self.title = entry_title.get().strip()
            self.config["code"] = txt_code.get("1.0", "end").strip()
            params = [p.strip() for p in entry_params.get().split(",") if p.strip()]
            self.config["params"] = params
            self.config["variable_name"] = entry_var.get().strip()
            self.text = f"Python: {self.config.get('variable_name', '')}" or "Python"
            try:
                compile(self.config["code"], "<string>", "exec")
            except Exception as e:
                messagebox.showwarning("Error de compilación", f"Error al compilar código:\n{traceback.format_exc()}", parent=dialog)
                return
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=4, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=4, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        code = self.config.get("code", "")
        params = self.config.get("params", [])
        var_name = self.config.get("variable_name", "respuesta")
        param_values = {}
        for p in params:
            value = context.get(p)
            if value is None:
                root = context.get("root")
                value = simpledialog.askstring("Parámetro", f"Ingrese valor para '{p}':", parent=root)
            param_values[p] = value
        try:
            compiled = compile(code, "<string>", "exec")
            local_vars = {}
            exec(compiled, {}, local_vars)
            if "func" not in local_vars:
                result = "Error: No se definió la función 'func'"
            else:
                result = local_vars["func"](**param_values)
        except Exception as e:
            result = f"Error al ejecutar código: {e}"
        context[var_name] = result
        print(f"Python: Resultado: {result}")
        return self.connected_to
