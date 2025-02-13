# controllers/diagram_controller.py
from models.flow_node import FlowNode
from models.graph_manager import GraphManager
from models.variable_manager import VariableManager
from models.ollama_client import OllamaClient
from tkinter import simpledialog, messagebox, Toplevel, StringVar, filedialog
from tkinter import ttk
import os, json, uuid
import tkinter as tk
import re

class DiagramController:
    def __init__(self, view):
        self.view = view
        self.graph_manager = GraphManager()
        self.variable_manager = VariableManager()
        self.nodes = {}         # node.id -> FlowNode
        self.node_views = {}    # node.id -> NodeView
        self.selected_node_id = None
        self.connection_start_id = None
        self.connection_start_branch = None  # "true" o "false" para nodos condicionales
        self.selected_connection_id = None
        self.deleting_connection = False
        self.start_x = None
        self.start_y = None
        # Al iniciar, se puede cargar un archivo de variables predeterminado (si existe)
        self.load_default_variables()

    def load_default_variables(self):
        default_file = "default_variables.json"
        if os.path.exists(default_file):
            try:
                with open(default_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.variable_manager.load_variables(data.get("variables", []))
                if self.view:
                    self.view.update_variables_panel(self.variable_manager.get_all_variables())
            except Exception as e:
                messagebox.showwarning("Advertencia", f"No se pudo cargar el archivo de variables predeterminado: {str(e)}")

    def save_flow(self):
        # Serializar nodos y variables a un diccionario
        flow_data = {}
        nodes_list = []
        for node in self.nodes.values():
            node_dict = {
                "id": node.id,
                "x": node.x,
                "y": node.y,
                "node_type": node.node_type,
                "text": node.text,
                "title": node.title,
                "config": node.config,
                "connected_to": node.connected_to.id if node.connected_to else None,
                "true_connection": node.true_connection.id if node.true_connection else None,
                "false_connection": node.false_connection.id if node.false_connection else None
            }
            nodes_list.append(node_dict)
        flow_data["nodes"] = nodes_list

        # Variables
        vars_list = []
        for var in self.variable_manager.get_all_variables():
            vars_list.append({
                "name": var.name,
                "var_type": var.var_type,
                "value": var.value
            })
        flow_data["variables"] = vars_list

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files","*.json")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(flow_data, f, indent=4)
                messagebox.showinfo("Guardar Flujo", f"Flujo guardado en: {file_path}")
            except Exception as e:
                messagebox.showwarning("Guardar Flujo", f"No se pudo guardar el archivo: {str(e)}")

    def load_flow(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files","*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                flow_data = json.load(f)
        except Exception as e:
            messagebox.showwarning("Cargar Flujo", f"Error al leer el archivo: {str(e)}")
            return

        # Limpiar flujo actual
        for node_view in list(self.node_views.values()):
            self.view.delete_node_view(node_view)
        self.nodes = {}
        self.node_views = {}

        # Cargar variables
        if "variables" in flow_data:
            self.variable_manager.load_variables(flow_data["variables"])
            self.view.update_variables_panel(self.variable_manager.get_all_variables())

        # Crear nodos
        for nd in flow_data.get("nodes", []):
            node = FlowNode(nd["x"], nd["y"], nd["node_type"], nd["text"], nd.get("title", ""))
            node.id = nd["id"]  # Restaurar el id original
            node.config = nd.get("config", {})
            self.nodes[node.id] = node

        # Crear vistas para cada nodo
        for node in self.nodes.values():
            node_view = self.view.create_node_view(node)
            self.node_views[node.id] = node_view

        # Establecer conexiones lógicas (en memoria, sin dibujar aún)
        for nd in flow_data.get("nodes", []):
            node = self.nodes[nd["id"]]
            if nd.get("connected_to"):
                target = self.nodes.get(nd["connected_to"])
                if target:
                    node.connected_to = target

            if node.node_type == "condicional":
                if nd.get("true_connection"):
                    target = self.nodes.get(nd["true_connection"])
                    if target:
                        node.true_connection = target
                if nd.get("false_connection"):
                    target = self.nodes.get(nd["false_connection"])
                    if target:
                        node.false_connection = target

        # Finalmente, dibujar las líneas en el canvas
        for node in self.nodes.values():
            if node.node_type == "condicional":
                if node.true_connection:
                    line_id = self.view.create_connection_view(node, node.true_connection, branch="true")
                    setattr(node, "true_connection_id", line_id)
                if node.false_connection:
                    line_id = self.view.create_connection_view(node, node.false_connection, branch="false")
                    setattr(node, "false_connection_id", line_id)
            else:
                if node.connected_to:
                    line_id = self.view.create_connection_view(node, node.connected_to)
                    setattr(node, "outgoing_connection_id", line_id)

        messagebox.showinfo("Cargar Flujo", f"Flujo cargado desde: {file_path}")

    # --- Gestión de Variables ---
    def handle_add_variable(self):
        dialog = Toplevel(self.view.root)
        dialog.title("Agregar Variable")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        lbl_name = ttk.Label(dialog, text="Nombre:")
        lbl_name.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_name = ttk.Entry(dialog, width=30)
        entry_name.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        lbl_type = ttk.Label(dialog, text="Tipo:")
        lbl_type.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        type_var = StringVar(value="string")
        cb_type = ttk.Combobox(dialog, textvariable=type_var, state="readonly",
                               values=["string", "integer", "boolean"])
        cb_type.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        lbl_value = ttk.Label(dialog, text="Valor (opcional):")
        lbl_value.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_value = ttk.Entry(dialog, width=30)
        entry_value.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        def on_ok():
            name = entry_name.get().strip()
            var_type = type_var.get()
            value = entry_value.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "El nombre es obligatorio", parent=dialog)
                return
            try:
                self.variable_manager.add_variable(name, var_type, value if value else None)
            except ValueError as ve:
                messagebox.showwarning("Advertencia", str(ve), parent=dialog)
                return
            dialog.destroy()
            self.view.update_variables_panel(self.variable_manager.get_all_variables())

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=3, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=3, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    # --- Configuración de Nodos ---
    def handle_node_configuration(self, event):
        try:
            clicked_item = self.view.canvas.find_closest(event.x, event.y)[0]
            tags = self.view.canvas.gettags(clicked_item)
            node_id = None
            for tag in tags:
                if tag in self.node_views:
                    node_id = tag
                    break
            if not node_id:
                return

            node = self.nodes[node_id]
            if node.node_type == "accion":
                self.show_action_config_dialog(node)
            elif node.node_type == "condicional":
                self.show_conditional_config_dialog(node)
            elif node.node_type == "multiples":
                self.show_multiples_config_dialog(node)
            elif node.node_type == "llm":
                self.show_llm_config_dialog(node)
            elif node.node_type == "python":
                self.show_python_config_dialog(node)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            # Reset any state here if needed
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    def show_action_config_dialog(self, node):
        # (Sin cambios sustanciales; solo configuración del nodo)
        dialog = Toplevel(self.view.root)
        dialog.title("Configurar Nodo de Acción")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if node.title:
            entry_title.insert(0, node.title)

        lbl_action = ttk.Label(dialog, text="Tipo de Acción:")
        lbl_action.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        current_action = node.config.get("action_type", "imprimir")
        action_type_var = StringVar(value=current_action)
        cb_action = ttk.Combobox(dialog, textvariable=action_type_var, state="readonly",
                                 values=["imprimir", "pregunta"])
        cb_action.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        lbl_print = ttk.Label(dialog, text="Texto a imprimir:")
        entry_print = ttk.Entry(dialog, width=40)
        if current_action == "imprimir":
            entry_print.insert(0, node.config.get("print_text", node.text))

        lbl_question = ttk.Label(dialog, text="Pregunta:")
        entry_question = ttk.Entry(dialog, width=40)
        lbl_variable = ttk.Label(dialog, text="Variable:")
        var_names = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
        variable_var = StringVar()

        if current_action == "pregunta":
            entry_question.insert(0, node.config.get("question", ""))
            variable_var.set(node.config.get("variable_name", var_names[0]))
        else:
            variable_var.set(var_names[0])

        cb_variable = ttk.Combobox(dialog, textvariable=variable_var, state="readonly", values=var_names)

        # Ajustar visibilidad inicial
        if current_action == "imprimir":
            lbl_print.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            entry_print.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        else:
            lbl_question.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            entry_question.grid(row=2, column=1, padx=10, pady=5, sticky="w")
            lbl_variable.grid(row=3, column=0, padx=10, pady=5, sticky="w")
            cb_variable.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        def update_fields(event=None):
            if action_type_var.get() == "imprimir":
                lbl_print.grid(row=2, column=0, padx=10, pady=5, sticky="w")
                entry_print.grid(row=2, column=1, padx=10, pady=5, sticky="w")

                lbl_question.grid_forget()
                entry_question.grid_forget()
                lbl_variable.grid_forget()
                cb_variable.grid_forget()
            else:
                lbl_print.grid_forget()
                entry_print.grid_forget()

                lbl_question.grid(row=2, column=0, padx=10, pady=5, sticky="w")
                entry_question.grid(row=2, column=1, padx=10, pady=5, sticky="w")
                lbl_variable.grid(row=3, column=0, padx=10, pady=5, sticky="w")
                cb_variable.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        cb_action.bind("<<ComboboxSelected>>", update_fields)

        def on_ok():
            title = entry_title.get().strip()
            node.title = title
            selected = action_type_var.get()
            if selected == "imprimir":
                text_value = entry_print.get().strip()
                if not text_value:
                    messagebox.showwarning("Advertencia", "Debe ingresar el texto a imprimir.", parent=dialog)
                    return
                node.config["action_type"] = "imprimir"
                node.config["print_text"] = text_value
                node.text = text_value
            else:
                question_text = entry_question.get().strip()
                if not question_text:
                    messagebox.showwarning("Advertencia", "Debe ingresar la pregunta.", parent=dialog)
                    return
                var_selected = variable_var.get()
                if var_selected == "<Crear nueva variable>":
                    self.handle_add_variable()
                    new_names = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
                    cb_variable['values'] = new_names
                    var_selected = new_names[1] if len(new_names) > 1 else ""
                    if not var_selected:
                        messagebox.showwarning("Advertencia", "No se pudo crear la variable.", parent=dialog)
                        return
                node.config["action_type"] = "pregunta"
                node.config["question"] = question_text
                node.config["variable_name"] = var_selected
                node.text = f"? {var_selected}"

            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=4, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=4, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def show_conditional_config_dialog(self, node):
        # (Implementación original, sin cambios lógicos)
        dialog = Toplevel(self.view.root)
        dialog.title("Configurar Nodo Condicional")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if node.title:
            entry_title.insert(0, node.title)

        lbl_info = ttk.Label(dialog, text="Defina las condiciones:")
        lbl_info.grid(row=1, column=0, columnspan=3, padx=10, pady=5)
        conditions_frame = ttk.Frame(dialog)
        conditions_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5)
        condition_entries = []

        def add_condition_row():
            row = len(condition_entries)
            lbl_var = ttk.Label(conditions_frame, text="Variable:")
            lbl_var.grid(row=row, column=0, padx=5, pady=3)
            cb_var = ttk.Combobox(conditions_frame, state="readonly",
                                  values=[var.name for var in self.variable_manager.get_all_variables()])
            cb_var.grid(row=row, column=1, padx=5, pady=3)
            lbl_op = ttk.Label(conditions_frame, text="Operador:")
            lbl_op.grid(row=row, column=2, padx=5, pady=3)
            cb_op = ttk.Combobox(conditions_frame, state="readonly", values=["==", "!=", ">", "<"])
            cb_op.grid(row=row, column=3, padx=5, pady=3)
            lbl_val = ttk.Label(conditions_frame, text="Valor:")
            lbl_val.grid(row=row, column=4, padx=5, pady=3)
            entry_val = ttk.Entry(conditions_frame, width=15)
            entry_val.grid(row=row, column=5, padx=5, pady=3)
            condition_entries.append({
                "variable": cb_var,
                "operator": cb_op,
                "value": entry_val
            })

        # Pre-cargar condiciones si existen
        if "conditions" in node.config:
            for cond in node.config["conditions"]:
                add_condition_row()
                last = condition_entries[-1]
                last["variable"].set(cond.get("variable"))
                last["operator"].set(cond.get("operator"))
                last["value"].insert(0, cond.get("value"))
        else:
            add_condition_row()

        lbl_logic = ttk.Label(dialog, text="Lógica entre condiciones:")
        lbl_logic.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        cb_logic = ttk.Combobox(dialog, state="readonly", values=["", "AND", "OR"])
        if "logical_operator" in node.config:
            cb_logic.set(node.config["logical_operator"])
        else:
            cb_logic.current(0)
        cb_logic.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        btn_add = ttk.Button(dialog, text="Agregar condición", command=add_condition_row)
        btn_add.grid(row=3, column=2, padx=10, pady=5)

        def on_ok():
            title = entry_title.get().strip()
            node.title = title
            conditions = []
            for cond in condition_entries:
                var_sel = cond["variable"].get().strip()
                op = cond["operator"].get().strip()
                val = cond["value"].get().strip()
                if not var_sel or not op or not val:
                    messagebox.showwarning("Advertencia", "Complete todos los campos de cada condición.", parent=dialog)
                    return
                conditions.append({
                    "variable": var_sel,
                    "operator": op,
                    "value": val
                })
            node.config["conditions"] = conditions
            node.config["logical_operator"] = cb_logic.get().strip()
            node.text = "Condicional"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=4, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=4, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def show_multiples_config_dialog(self, node):
        # (Implementación original, sin cambios relevantes)
        dialog = Toplevel(self.view.root)
        dialog.title("Configurar Nodo de Múltiples Respuestas")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if node.title:
            entry_title.insert(0, node.title)

        lbl_question = ttk.Label(dialog, text="Pregunta:")
        lbl_question.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entry_question = ttk.Entry(dialog, width=40)
        entry_question.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        if "question" in node.config:
            entry_question.insert(0, node.config.get("question"))

        lbl_resp = ttk.Label(dialog, text="Respuestas:")
        lbl_resp.grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        responses_frame = ttk.Frame(dialog)
        responses_frame.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        response_entries = []

        def add_response_row():
            row = len(response_entries)
            entry_resp = ttk.Entry(responses_frame, width=30)
            entry_resp.grid(row=row, column=0, padx=5, pady=3, sticky="w")
            response_entries.append(entry_resp)

        if "responses" in node.config:
            for resp in node.config.get("responses"):
                add_response_row()
                response_entries[-1].insert(0, resp)
        else:
            add_response_row()

        btn_add_resp = ttk.Button(dialog, text="Agregar Respuesta", command=add_response_row)
        btn_add_resp.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        lbl_variable = ttk.Label(dialog, text="Variable:")
        lbl_variable.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        var_names = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
        variable_var = StringVar()
        if "variable_name" in node.config:
            variable_var.set(node.config.get("variable_name"))
        else:
            variable_var.set(var_names[0])
        cb_variable = ttk.Combobox(dialog, textvariable=variable_var, state="readonly", values=var_names)
        cb_variable.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        def on_ok():
            title = entry_title.get().strip()
            node.title = title
            question = entry_question.get().strip()
            if not question:
                messagebox.showwarning("Advertencia", "Debe ingresar la pregunta.", parent=dialog)
                return
            responses = []
            for entry in response_entries:
                resp = entry.get().strip()
                if resp:
                    responses.append(resp)
            if not responses:
                messagebox.showwarning("Advertencia", "Debe ingresar al menos una respuesta.", parent=dialog)
                return

            var_sel = variable_var.get()
            if var_sel == "<Crear nueva variable>":
                self.handle_add_variable()
                new_names = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
                cb_variable['values'] = new_names
                var_sel = new_names[1] if len(new_names) > 1 else ""
                if not var_sel:
                    messagebox.showwarning("Advertencia", "No se pudo crear la variable.", parent=dialog)
                    return

            node.config["action_type"] = "multiples"
            node.config["question"] = question
            node.config["responses"] = responses
            node.config["variable_name"] = var_sel
            node.text = f"? {var_sel}"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=5, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=5, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def show_llm_config_dialog(self, node):
        dialog = Toplevel(self.view.root)
        dialog.title("Configurar Nodo LLM")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        def setup_field(row, label_text, config_key):
            lbl = ttk.Label(dialog, text=label_text)
            lbl.grid(row=row, column=0, padx=10, pady=5, sticky="w")
            cb = ttk.Combobox(dialog, state="readonly")
            options = ["<Escribir libre>"] + [var.name for var in self.variable_manager.get_all_variables()]
            cb['values'] = options
            cb.current(0)
            cb.grid(row=row, column=1, padx=10, pady=5, sticky="w")

            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=row, column=2, padx=10, pady=5, sticky="w")

            # Pre-carga si existe en config
            if config_key in node.config:
                cfg = node.config.get(config_key)
                if cfg.get("type") == "variable":
                    if cfg.get("value") in options:
                        cb.set(cfg.get("value"))
                    else:
                        cb.set("<Escribir libre>")
                    entry.delete(0, tk.END)
                    entry.insert(0, "")
                    entry.config(state="disabled")
                else:
                    cb.set("<Escribir libre>")
                    entry.delete(0, tk.END)
                    entry.insert(0, cfg.get("value", ""))
                    entry.config(state="normal")
            else:
                cb.set("<Escribir libre>")
                entry.config(state="normal")

            def on_field_change(event=None):
                if cb.get() == "<Escribir libre>":
                    entry.config(state="normal")
                else:
                    entry.config(state="disabled")

            cb.bind("<<ComboboxSelected>>", on_field_change)
            return (cb, entry)

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if node.title:
            entry_title.insert(0, node.title)

        (cb_model, entry_model) = setup_field(1, "Modelo:", "model")
        (cb_personality, entry_personality) = setup_field(2, "Personalidad:", "personality")
        (cb_instructions, entry_instructions) = setup_field(3, "Instrucciones:", "instructions")
        (cb_context, entry_context) = setup_field(4, "Contexto (opcional):", "context")
        (cb_prompt, entry_prompt) = setup_field(5, "prompt (opcional):", "prompt")

        lbl_variable = ttk.Label(dialog, text="Variable de salida:")
        lbl_variable.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        var_options = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
        variable_var = tk.StringVar()
        variable_var.set(var_options[0])
        cb_variable = ttk.Combobox(dialog, textvariable=variable_var, state="readonly", values=var_options)
        cb_variable.grid(row=6, column=1, padx=10, pady=5, sticky="w")

        def on_ok():
            title = entry_title.get().strip()
            node.title = title

            def resolve_field(cb, entry):
                if cb.get() == "<Escribir libre>":
                    return {"type": "free", "value": entry.get().strip()}
                else:
                    return {"type": "variable", "value": cb.get()}

            node.config["model"] = resolve_field(cb_model, entry_model)
            node.config["personality"] = resolve_field(cb_personality, entry_personality)
            node.config["instructions"] = resolve_field(cb_instructions, entry_instructions)
            node.config["context"] = resolve_field(cb_context, entry_context)
            node.config["prompt"] = resolve_field(cb_prompt, entry_prompt)

            var_sel = variable_var.get()
            if var_sel == "<Crear nueva variable>":
                self.handle_add_variable()
                new_options = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
                cb_variable['values'] = new_options
                var_sel = new_options[1] if len(new_options) > 1 else ""
                if not var_sel:
                    messagebox.showwarning("Advertencia", "No se pudo crear la variable.", parent=dialog)
                    return

            node.config["variable_name"] = var_sel
            node.config["action_type"] = "llm"
            node.text = f"LLM: {var_sel}"

            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=7, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=7, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def show_python_config_dialog(self, node):
        dialog = Toplevel(self.view.root)
        dialog.title("Configurar Nodo Python")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=50)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if node.title:
            entry_title.insert(0, node.title)

        lbl_code = ttk.Label(dialog, text="Código (defina una función 'func'):")
        lbl_code.grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        txt_code = tk.Text(dialog, width=60, height=10)
        txt_code.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        if "code" in node.config:
            txt_code.insert("1.0", node.config.get("code"))

        lbl_params = ttk.Label(dialog, text="Parámetros (coma-separados):")
        lbl_params.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_params = ttk.Entry(dialog, width=50)
        entry_params.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        if "params" in node.config:
            entry_params.insert(0, ", ".join(node.config.get("params")))

        lbl_variable = ttk.Label(dialog, text="Variable de salida:")
        lbl_variable.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        var_names = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
        variable_var = StringVar()
        variable_var.set(var_names[0])
        cb_variable = ttk.Combobox(dialog, textvariable=variable_var, state="readonly", values=var_names)
        cb_variable.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        def on_ok():
            title = entry_title.get().strip()
            node.title = title
            code_text = txt_code.get("1.0", tk.END).strip()
            if not code_text:
                messagebox.showwarning("Advertencia", "Debe ingresar el código.", parent=dialog)
                return
            try:
                compile(code_text, "<string>", "exec")
            except Exception as e:
                messagebox.showwarning("Advertencia", f"Error de compilación: {str(e)}", parent=dialog)
                return

            params_str = entry_params.get().strip()
            params = [p.strip() for p in params_str.split(",")] if params_str else []

            node.config["code"] = code_text
            node.config["params"] = params

            var_sel = variable_var.get()
            if var_sel == "<Crear nueva variable>":
                self.handle_add_variable()
                new_names = ["<Crear nueva variable>"] + [var.name for var in self.variable_manager.get_all_variables()]
                cb_variable['values'] = new_names
                var_sel = new_names[1] if len(new_names) > 1 else ""
                if not var_sel:
                    messagebox.showwarning("Advertencia", "No se pudo crear la variable.", parent=dialog)
                    return

            node.config["variable_name"] = var_sel
            node.config["action_type"] = "python"
            node.text = f"Python: {var_sel}"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=4, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=4, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    # --- Creación y eliminación de nodos ---
    def handle_add_node(self, node_type):
        try:
            if node_type == "inicio" and any(n.node_type == "inicio" for n in self.nodes.values()):
                self.view.show_warning("Solo puede haber un nodo de inicio")
                return
            x, y = 100, len(self.nodes) * 100
            text = f"{node_type.capitalize()} {len(self.nodes)+1}"
            node = FlowNode(x, y, node_type, text)
            self.nodes[node.id] = node
            self.graph_manager.add_node(node)
            node_view = self.view.create_node_view(node)
            self.node_views[node.id] = node_view
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al crear nodo: {str(e)}")

    def handle_delete_node(self, event=None):
        try:
            if self.selected_node_id and self.selected_node_id in self.nodes:
                node = self.nodes[self.selected_node_id]
                if node.node_type == "inicio":
                    self.view.show_warning("No se puede eliminar el nodo de inicio")
                    return

                # Eliminar conexiones
                if node.connected_from:
                    conn_id = getattr(node.connected_from, "outgoing_connection_id", None)
                    if conn_id:
                        self.view.delete_connection_view(conn_id)
                    node.connected_from.connected_to = None

                if node.node_type != "condicional":
                    if node.connected_to:
                        conn_id = getattr(node, "outgoing_connection_id", None)
                        if conn_id:
                            self.view.delete_connection_view(conn_id)
                        node.connected_to.connected_from = None
                else:
                    if hasattr(node, "true_connection_id"):
                        self.view.delete_connection_view(node.true_connection_id)
                    if hasattr(node, "false_connection_id"):
                        self.view.delete_connection_view(node.false_connection_id)

                self.view.delete_node_view(self.node_views[node.id])
                self.graph_manager.remove_node(node.id)
                del self.nodes[node.id]
                del self.node_views[node.id]
                self.selected_node_id = None
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al eliminar nodo: {str(e)}")
        finally:
            # Reset state to be safe
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    def handle_start_connection(self):
        try:
            self.connection_start_id = None
            self.connection_start_branch = None
            self.view.show_info("Conectar Nodos",
                "Haga clic en el puerto de salida del nodo origen y luego en el puerto de entrada del nodo destino.\nPara nodos condicionales, seleccione la salida 'True' o 'False'.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            self.connection_start_id = None
            self.connection_start_branch = None

    def handle_start_delete_connection(self):
        try:
            self.deleting_connection = True
            self.view.show_info("Eliminar Conexión", "Haga clic en la conexión que desea eliminar")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            self.deleting_connection = False

    # --- Eventos del Canvas ---
    def handle_canvas_click(self, event):
        try:
            clicked_item = self.view.canvas.find_closest(event.x, event.y)[0]
            tags = self.view.canvas.gettags(clicked_item)

            if self.deleting_connection:
                if "connection" in tags:
                    self.selected_connection_id = clicked_item
                    self.handle_delete_connection()
                else:
                    self.view.show_info("Info", "Por favor, haga clic en una conexión.")
                self.deleting_connection = False
                return

            if self.connection_start_id:
                if "connection_point" in tags and "input_point" in tags:
                    target_node_id = None
                    for tag in tags:
                        if tag in self.node_views:
                            target_node_id = tag
                            break
                    if (not target_node_id) or (target_node_id == self.connection_start_id):
                        self.view.show_warning("No se puede conectar un nodo consigo mismo")
                        if self.connection_start_branch:
                            branch_tag = "output_true" if self.connection_start_branch=="true" else "output_false"
                            self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids[branch_tag], fill="black")
                        else:
                            self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids["output"], fill="black")
                        self.connection_start_id = None
                        self.connection_start_branch = None
                        return

                    start_node = self.nodes[self.connection_start_id]
                    target_node = self.nodes[target_node_id]
                    if start_node.node_type == "condicional":
                        if (start_node.true_connection and self.connection_start_branch=="true") or \
                           (start_node.false_connection and self.connection_start_branch=="false"):
                            self.view.show_warning("La salida ya tiene conexión")
                            branch_tag = "output_true" if self.connection_start_branch=="true" else "output_false"
                            self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids[branch_tag], fill="black")
                            self.connection_start_id = None
                            self.connection_start_branch = None
                            return
                        connection_id = self.view.create_connection_view(start_node, target_node, branch=self.connection_start_branch)
                        if self.connection_start_branch == "true":
                            start_node.true_connection = target_node
                            setattr(start_node, "true_connection_id", connection_id)
                        else:
                            start_node.false_connection = target_node
                            setattr(start_node, "false_connection_id", connection_id)
                    else:
                        if start_node.connected_to:
                            self.view.show_warning("El nodo ya tiene conexión establecida")
                            self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids["output"], fill="black")
                            self.connection_start_id = None
                            return
                        connection_id = self.view.create_connection_view(start_node, target_node)
                        start_node.connected_to = target_node
                        setattr(start_node, "outgoing_connection_id", connection_id)

                    # Resetear el color y estado
                    if self.connection_start_branch:
                        branch_tag = "output_true" if self.connection_start_branch=="true" else "output_false"
                        self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids[branch_tag], fill="black")
                    else:
                        self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids["output"], fill="black")
                    self.connection_start_id = None
                    self.connection_start_branch = None
                return

            # Si no es conexión, tal vez estamos seleccionando un nodo
            if self.selected_node_id and self.selected_node_id in self.node_views:
                self.view.unhighlight_node_view(self.node_views[self.selected_node_id])
                self.selected_node_id = None

            node_id = None
            for tag in tags:
                if tag in self.node_views:
                    node_id = tag
                    break
            if node_id:
                self.selected_node_id = node_id
                self.start_x = event.x
                self.start_y = event.y
                self.view.highlight_node_view(self.node_views[node_id])

                # ¿Es un punto de conexión de salida?
                if "connection_point" in tags:
                    if "output_point" in tags:
                        self.connection_start_id = node_id
                    elif "output_true" in tags:
                        self.connection_start_id = node_id
                        self.connection_start_branch = "true"
                    elif "output_false" in tags:
                        self.connection_start_id = node_id
                        self.connection_start_branch = "false"

                    if self.connection_start_branch:
                        branch_tag = "output_true" if self.connection_start_branch=="true" else "output_false"
                        self.view.canvas.itemconfig(self.node_views[node_id].ids[branch_tag], fill="red")
                    else:
                        self.view.canvas.itemconfig(self.node_views[node_id].ids["output"], fill="red")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    def handle_canvas_drag(self, event):
        try:
            if self.selected_node_id and self.selected_node_id in self.nodes:
                dx = event.x - self.start_x
                dy = event.y - self.start_y
                node = self.nodes[self.selected_node_id]
                node.x += dx
                node.y += dy
                self.view.update_node_view(self.node_views[node.id])

                if node.node_type == "condicional":
                    if node.true_connection and hasattr(node, "true_connection_id"):
                        self.view.update_connection_view(node.true_connection_id, node, node.true_connection, branch="true")
                    if node.false_connection and hasattr(node, "false_connection_id"):
                        self.view.update_connection_view(node.false_connection_id, node, node.false_connection, branch="false")
                else:
                    if node.connected_to and hasattr(node, "outgoing_connection_id"):
                        self.view.update_connection_view(node.outgoing_connection_id, node, node.connected_to)

                # Actualizar conexiones de otros nodos que apuntan a este
                for other in self.nodes.values():
                    if other == node:
                        continue
                    if hasattr(other, "outgoing_connection_id") and other.connected_to == node:
                        self.view.update_connection_view(other.outgoing_connection_id, other, node)
                    if other.node_type == "condicional":
                        if other.true_connection == node and hasattr(other, "true_connection_id"):
                            self.view.update_connection_view(other.true_connection_id, other, node, branch="true")
                        if other.false_connection == node and hasattr(other, "false_connection_id"):
                            self.view.update_connection_view(other.false_connection_id, other, node, branch="false")

                self.start_x = event.x
                self.start_y = event.y
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    def handle_canvas_release(self, event):
        # Si quieres capturar errores también aquí, puedes usar try/except:
        try:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    def handle_delete_connection(self):
        try:
            for node in self.nodes.values():
                if hasattr(node, "outgoing_connection_id") and node.outgoing_connection_id == self.selected_connection_id:
                    target_node = node.connected_to
                    self.view.delete_connection_view(self.selected_connection_id)
                    node.connected_to = None
                    if target_node:
                        target_node.connected_from = None
                    self.graph_manager.remove_edge(node, target_node)
                    delattr(node, "outgoing_connection_id")
                    self.selected_connection_id = None
                    return

                if node.node_type == "condicional":
                    if hasattr(node, "true_connection_id") and node.true_connection_id == self.selected_connection_id:
                        self.view.delete_connection_view(self.selected_connection_id)
                        node.true_connection = None
                        delattr(node, "true_connection_id")
                        self.selected_connection_id = None
                        return
                    if hasattr(node, "false_connection_id") and node.false_connection_id == self.selected_connection_id:
                        self.view.delete_connection_view(self.selected_connection_id)
                        node.false_connection = None
                        delattr(node, "false_connection_id")
                        self.selected_connection_id = None
                        return
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al eliminar la conexión: {str(e)}")
        finally:
            self.deleting_connection = False
            self.selected_connection_id = None

    def handle_delete_key(self, event):
        try:
            self.handle_delete_node()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
        finally:
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    # --- Ejecución del flujo con memoria ---
    def handle_execute_flow(self):
        start_node = None
        for node in self.nodes.values():
            if node.node_type == "inicio":
                start_node = node
                break
        if not start_node:
            self.view.show_warning("Debe existir un nodo de inicio")
            return

        memory = {}
        current_node = start_node
        print("Ejecución del Flujo:")

        while current_node:
            if current_node.node_type == "accion":
                action_type = current_node.config.get("action_type", "imprimir")
                if action_type == "imprimir":
                    text_to_print = current_node.config.get("print_text", current_node.text)
                    print(f"Acción Imprimir: {text_to_print}")
                elif action_type == "pregunta":
                    question = current_node.config.get("question", "Ingrese respuesta:")
                    var_name = current_node.config.get("variable_name", "respuesta")
                    self.view.root.lift()
                    self.view.root.attributes("-topmost", True)
                    self.view.root.update_idletasks()

                    # Reemplazar variables embebidas si las hay
                    posible_variables = re.findall(r'\$\{([^}]+)\}', question)
                    for var in posible_variables:
                        var_obj = self.variable_manager.get_variable(var)
                        if var_obj:
                            question = question.replace(f"${{{var}}}", str(var_obj.value))

                    answer = simpledialog.askstring("Pregunta", question, parent=self.view.root)
                    self.view.root.attributes("-topmost", False)
                    print(f"Pregunta: {question} | Respuesta: {answer}")
                    memory[var_name] = answer
                    self.variable_manager.update_variable(var_name, answer)

            elif current_node.node_type == "condicional":
                conditions = current_node.config.get("conditions", [])
                logical_op = current_node.config.get("logical_operator", "")
                result = None
                for cond in conditions:
                    var_name = cond.get("variable")
                    operator = cond.get("operator")
                    value = cond.get("value")
                    var_obj = self.variable_manager.get_variable(var_name)
                    var_val = var_obj.value if var_obj else None
                    condition_result = False
                    if operator == "==":
                        condition_result = str(var_val) == value
                    elif operator == "!=":
                        condition_result = str(var_val) != value
                    elif operator == ">":
                        try:
                            condition_result = float(var_val) > float(value)
                        except:
                            condition_result = False
                    elif operator == "<":
                        try:
                            condition_result = float(var_val) < float(value)
                        except:
                            condition_result = False

                    if result is None:
                        result = condition_result
                    else:
                        if logical_op.upper() == "AND":
                            result = result and condition_result
                        elif logical_op.upper() == "OR":
                            result = result or condition_result
                        else:
                            # Si no hay "AND"/"OR" explícito, se toma la última
                            result = condition_result

                if result:
                    print("Condicional: VERDADERO")
                    current_node = current_node.true_connection
                    continue
                else:
                    print("Condicional: FALSO")
                    current_node = current_node.false_connection
                    continue

            elif current_node.node_type == "multiples":
                question = current_node.config.get("question", "Seleccione respuesta:")
                responses = current_node.config.get("responses", [])
                var_name = current_node.config.get("variable_name", "respuesta")
                choice = self.show_multiples_response_dialog(question, responses)
                print(f"Múltiples: {question} | Respuesta: {choice}")
                memory[var_name] = choice
                self.variable_manager.update_variable(var_name, choice)

            elif current_node.node_type == "llm":
                def resolve_field(cfg):
                    if cfg.get("type") == "variable":
                        var_obj = self.variable_manager.get_variable(cfg.get("value"))
                        return var_obj.value if var_obj else ""
                    else:
                        return cfg.get("value", "")

                model_cfg = current_node.config.get("model", {"type": "free", "value": ""})
                personality_cfg = current_node.config.get("personality", {"type": "free", "value": ""})
                instructions_cfg = current_node.config.get("instructions", {"type": "free", "value": ""})
                context_cfg = current_node.config.get("context", {"type": "free", "value": ""})
                prompt_cfg = current_node.config.get("prompt", {"type": "free", "value": ""})

                model = resolve_field(model_cfg)
                personality = resolve_field(personality_cfg)
                instructions = resolve_field(instructions_cfg)
                context = resolve_field(context_cfg)
                prompt = resolve_field(prompt_cfg)

                if prompt == "":
                    prompt = simpledialog.askstring("LLM Prompt", "Ingrese su pregunta:", parent=self.view.root)

                # Reemplazar variables embebidas en prompt
                posible_variables = re.findall(r'\$\{([^}]+)\}', prompt)
                for var in posible_variables:
                    var_obj = self.variable_manager.get_variable(var)
                    if var_obj:
                        prompt = prompt.replace(f"${{{var}}}", str(var_obj.value))

                message = {
                    "personality": personality,
                    "instructions": instructions,
                    "prompt": prompt,
                    "context": context
                }
                try:
                    client = OllamaClient(model)
                    answer = client.chat(message)
                except Exception as e:
                    answer = f"Error en LLM: {str(e)}"
                print(f"LLM: {prompt} | Respuesta: {answer}")
                var_name = current_node.config.get("variable_name", "respuesta")
                memory[var_name] = answer
                self.variable_manager.update_variable(var_name, answer)

            elif current_node.node_type == "python":
                code_text = current_node.config.get("code", "")
                params_list = current_node.config.get("params", [])
                output_var = current_node.config.get("variable_name", "respuesta")
                param_values = {}
                for param in params_list:
                    check_variable = self.variable_manager.get_variable(param)
                    if check_variable:
                        value = check_variable.value
                    else:
                        value = simpledialog.askstring("Parámetro", f"Ingrese valor para el parámetro '{param}':", parent=self.view.root)
                    param_values[param] = value

                try:
                    compiled_code = compile(code_text, "<string>", "exec")
                    local_vars = {}
                    exec(compiled_code, {}, local_vars)
                    if "func" not in local_vars:
                        answer = "Error: No se definió la función 'func'"
                    else:
                        answer = local_vars["func"](**param_values)
                except Exception as e:
                    answer = f"Error al ejecutar código: {str(e)}"

                print(f"Python: Resultado: {answer}")
                memory[output_var] = answer
                self.variable_manager.update_variable(output_var, answer)
            else:
                print(f"Ejecutando: {current_node.text}")

            current_node = current_node.connected_to

        # Guardar estado de "memoria"
        memory_folder = "memoria"
        if not os.path.exists(memory_folder):
            os.makedirs(memory_folder)
        mem_id = str(uuid.uuid4())
        filename = os.path.join(memory_folder, f"{mem_id}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)

        print("Flujo completado exitosamente")
        print("Memoria guardada en:", filename)

    def show_multiples_response_dialog(self, question, responses):
        dialog = Toplevel(self.view.root)
        dialog.title("Pregunta - Múltiples Respuestas")
        dialog.transient(self.view.root)
        dialog.wait_visibility()
        dialog.grab_set()

        lbl_question = ttk.Label(dialog, text=question)
        lbl_question.pack(padx=10, pady=10)

        selected_var = tk.StringVar()
        for resp in responses:
            rb = ttk.Radiobutton(dialog, text=resp, variable=selected_var, value=resp)
            rb.pack(anchor="w", padx=20, pady=5)

        def on_ok():
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.pack(padx=10, pady=10)
        dialog.wait_window(dialog)
        return selected_var.get()

def main():
    controller = DiagramController(None)
    from views.diagram_view import DiagramView
    view = DiagramView(controller)
    controller.view = view
    view.mainloop()

if __name__ == "__main__":
    main()
