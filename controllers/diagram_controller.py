# controllers/diagram_controller.py
from models.node_factory import NodeFactory
from models.graph_manager import GraphManager
from models.variable_manager import VariableManager
from models.ollama_client import OllamaClient
import os, json, uuid, re
import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, filedialog
from tkinter import ttk

class DiagramController:
    def __init__(self, view):
        self.view = view
        self.graph_manager = GraphManager()
        self.variable_manager = VariableManager()
        self.nodes = {}         # node.id -> instancia de FlowNode (o sus subclases)
        self.node_views = {}    # node.id -> NodeView
        self.selected_node_id = None
        self.connection_start_id = None
        self.connection_start_branch = None  # Para nodos condicionales
        self.selected_connection_id = None
        self.deleting_connection = False
        self.start_x = None
        self.start_y = None
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
                # Para conexiones, almacenamos el id del nodo conectado (si existe)
                "connected_to": node.connected_to.id if node.connected_to else None,
                # Para nodos condicionales (si aplicable)
                "true_connection": getattr(node, "true_connection", None).id if getattr(node, "true_connection", None) else None,
                "false_connection": getattr(node, "false_connection", None).id if getattr(node, "false_connection", None) else None
            }
            nodes_list.append(node_dict)
        flow_data["nodes"] = nodes_list

        # Serializar variables
        vars_list = []
        for var in self.variable_manager.get_all_variables():
            vars_list.append({
                "name": var.name,
                "var_type": var.var_type,
                "value": var.value
            })
        flow_data["variables"] = vars_list

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(flow_data, f, indent=4)
                messagebox.showinfo("Guardar Flujo", f"Flujo guardado en: {file_path}")
            except Exception as e:
                messagebox.showwarning("Guardar Flujo", f"No se pudo guardar el archivo: {str(e)}")

    def load_flow(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
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

        # Crear nodos usando la factoría (se espera que cada nodo se configure de forma propia)
        for nd in flow_data.get("nodes", []):
            node = NodeFactory.create_node(nd["node_type"], nd["x"], nd["y"])
            node.id = nd["id"]  # Restaurar el id original
            node.text = nd["text"]
            node.title = nd.get("title", "")
            node.config = nd.get("config", {})
            self.nodes[node.id] = node

        # Crear vistas para cada nodo
        for node in self.nodes.values():
            node_view = self.view.create_node_view(node)
            self.node_views[node.id] = node_view

        # Establecer conexiones lógicas
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

        # Dibujar conexiones en el canvas
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
        type_var = tk.StringVar(value="string")
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
            except Exception as ve:
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
            # Ahora delegamos la configuración al nodo mismo
            node.configure(self.view.root, self.variable_manager)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")
            self.connection_start_id = None
            self.connection_start_branch = None
            self.deleting_connection = False
            self.selected_node_id = None

    # --- Creación y eliminación de nodos ---
    def handle_add_node(self, node_type):
        try:
            if node_type == "inicio" and any(n.node_type == "inicio" for n in self.nodes.values()):
                self.view.show_warning("Solo puede haber un nodo de inicio")
                return
            x, y = 100, len(self.nodes) * 100
            node = NodeFactory.create_node(node_type, x, y)
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

                # Eliminar conexiones entrantes y salientes
                if node.connected_from:
                    conn_id = getattr(node.connected_from, "outgoing_connection_id", None)
                    if conn_id:
                        self.view.delete_connection_view(conn_id)
                    node.connected_from.connected_to = None

                if node.connected_to:
                    conn_id = getattr(node, "outgoing_connection_id", None)
                    if conn_id:
                        self.view.delete_connection_view(conn_id)
                    node.connected_to.connected_from = None

                self.view.delete_node_view(self.node_views[node.id])
                self.graph_manager.remove_node(node.id)
                del self.nodes[node.id]
                del self.node_views[node.id]
                self.selected_node_id = None
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al eliminar nodo: {str(e)}")
        finally:
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
                        if (hasattr(start_node, "true_connection") and start_node.true_connection and self.connection_start_branch=="true") or \
                           (hasattr(start_node, "false_connection") and start_node.false_connection and self.connection_start_branch=="false"):
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
                    if self.connection_start_branch:
                        branch_tag = "output_true" if self.connection_start_branch=="true" else "output_false"
                        self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids[branch_tag], fill="black")
                    else:
                        self.view.canvas.itemconfig(self.node_views[self.connection_start_id].ids["output"], fill="black")
                    self.connection_start_id = None
                    self.connection_start_branch = None
                return

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
                if node.connected_to and hasattr(node, "outgoing_connection_id"):
                    self.view.update_connection_view(node.outgoing_connection_id, node, node.connected_to)
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

    # --- Ejecución del flujo ---
    def handle_execute_flow(self):
        start_node = None
        for node in self.nodes.values():
            if node.node_type == "inicio":
                start_node = node
                break
        if not start_node:
            self.view.show_warning("Debe existir un nodo de inicio")
            return

        context = {"root": self.view.root}
        current_node = start_node
        print("Ejecución del Flujo:")

        while current_node:
            # Cada nodo se encarga de ejecutar su acción y retornar el siguiente
            current_node = current_node.execute(context)

        memory_folder = "memoria"
        if not os.path.exists(memory_folder):
            os.makedirs(memory_folder)
        mem_id = str(uuid.uuid4())
        filename = os.path.join(memory_folder, f"{mem_id}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=4)
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
