# models/condicional_node.py
from models.nodes import FlowNode
from tkinter import Toplevel, ttk, messagebox

class CondicionalNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "condicional", "Condicional", "Condicional")
        self.config["conditions"] = []  # Lista de condiciones (cada una es un dict con variable, operador y valor)
        self.config["logical_operator"] = "AND"

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.title("Configurar Nodo Condicional")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        entry_title.insert(0, self.title)

        lbl_info = ttk.Label(dialog, text="Definir condiciones:")
        lbl_info.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        conditions_frame = ttk.Frame(dialog)
        conditions_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        condition_entries = []

        def add_condition():
            row = len(condition_entries)
            lbl_var = ttk.Label(conditions_frame, text="Variable:")
            lbl_var.grid(row=row, column=0, padx=5, pady=3)
            entry_var = ttk.Entry(conditions_frame, width=15)
            entry_var.grid(row=row, column=1, padx=5, pady=3)
            lbl_op = ttk.Label(conditions_frame, text="Operador:")
            lbl_op.grid(row=row, column=2, padx=5, pady=3)
            entry_op = ttk.Entry(conditions_frame, width=5)
            entry_op.grid(row=row, column=3, padx=5, pady=3)
            lbl_val = ttk.Label(conditions_frame, text="Valor:")
            lbl_val.grid(row=row, column=4, padx=5, pady=3)
            entry_val = ttk.Entry(conditions_frame, width=15)
            entry_val.grid(row=row, column=5, padx=5, pady=3)
            condition_entries.append((entry_var, entry_op, entry_val))

        # Pre-cargar condiciones si existen
        for cond in self.config.get("conditions", []):
            add_condition()
            entry_var, entry_op, entry_val = condition_entries[-1]
            entry_var.insert(0, cond.get("variable", ""))
            entry_op.insert(0, cond.get("operator", ""))
            entry_val.insert(0, cond.get("value", ""))
        if not self.config.get("conditions"):
            add_condition()

        lbl_logic = ttk.Label(dialog, text="Operador lógico (AND/OR):")
        lbl_logic.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_logic = ttk.Entry(dialog, width=20)
        entry_logic.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        entry_logic.insert(0, self.config.get("logical_operator", "AND"))

        def on_ok():
            self.title = entry_title.get().strip()
            conditions = []
            for entry_var, entry_op, entry_val in condition_entries:
                var_name = entry_var.get().strip()
                op = entry_op.get().strip()
                val = entry_val.get().strip()
                if var_name and op and val:
                    conditions.append({"variable": var_name, "operator": op, "value": val})
                else:
                    messagebox.showwarning("Advertencia", "Complete todos los campos en cada condición.", parent=dialog)
                    return
            self.config["conditions"] = conditions
            self.config["logical_operator"] = entry_logic.get().strip()
            self.text = "Condicional"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=4, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=4, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        conditions = self.config.get("conditions", [])
        logical_op = self.config.get("logical_operator", "AND").upper()
        result = None
        for cond in conditions:
            var_name = cond.get("variable")
            operator = cond.get("operator")
            value = cond.get("value")
            var_val = context.get(var_name)
            cond_result = False
            if operator == "==":
                cond_result = str(var_val) == value
            elif operator == "!=":
                cond_result = str(var_val) != value
            elif operator == ">":
                try:
                    cond_result = float(var_val) > float(value)
                except:
                    cond_result = False
            elif operator == "<":
                try:
                    cond_result = float(var_val) < float(value)
                except:
                    cond_result = False
            if result is None:
                result = cond_result
            else:
                if logical_op == "AND":
                    result = result and cond_result
                elif logical_op == "OR":
                    result = result or cond_result
                else:
                    result = cond_result
        if result:
            print("Condicional: VERDADERO")
            return self.true_connection
        else:
            print("Condicional: FALSO")
            return self.false_connection
