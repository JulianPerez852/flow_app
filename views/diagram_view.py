# views/diagram_view.py
import tkinter as tk
from tkinter import messagebox

class NodeView:
    def __init__(self, node, canvas, ids):
        self.node = node
        self.canvas = canvas
        self.ids = ids

class DiagramView:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Diagrama de Flujo")
        
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel de Variables
        self.variables_panel = tk.Frame(self.main_frame, width=200, bg="lightgray")
        self.variables_panel.pack(side=tk.LEFT, fill=tk.Y)
        self._setup_variables_panel()
        
        # Contenedor del Canvas con scrollbars
        self.canvas_container = tk.Frame(self.main_frame)
        self.canvas_container.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.vbar = tk.Scrollbar(self.canvas_container, orient=tk.VERTICAL)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hbar = tk.Scrollbar(self.canvas_container, orient=tk.HORIZONTAL)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas = tk.Canvas(self.canvas_container, bg="white",
                                xscrollcommand=self.hbar.set,
                                yscrollcommand=self.vbar.set,
                                scrollregion=(0, 0, 3000, 3000))
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.hbar.config(command=self.canvas.xview)
        self.vbar.config(command=self.canvas.yview)
        
        # Toolbar
        self.toolbar = tk.Frame(self.main_frame)
        self.toolbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.setup_toolbar()
        
        self.canvas.bind("<Button-1>", self.controller.handle_canvas_click)
        self.canvas.bind("<B1-Motion>", self.controller.handle_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.controller.handle_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.controller.handle_node_configuration)
        self.root.bind("<Delete>", self.controller.handle_delete_key)
    
    def _setup_variables_panel(self):
        lbl = tk.Label(self.variables_panel, text="Variables", bg="lightgray", font=("Arial", 12, "bold"))
        lbl.pack(padx=5, pady=5)
        self.var_listbox = tk.Listbox(self.variables_panel)
        self.var_listbox.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        btn = tk.Button(self.variables_panel, text="Agregar Variable", command=self.controller.handle_add_variable)
        btn.pack(padx=5, pady=5, fill=tk.X)
    
    def update_variables_panel(self, variables):
        self.var_listbox.delete(0, tk.END)
        for var in variables:
            self.var_listbox.insert(tk.END, str(var))
    
    def setup_toolbar(self):
        btn_inicio = tk.Button(self.toolbar, text="Inicio", command=lambda: self.controller.handle_add_node("inicio"))
        btn_inicio.pack(fill=tk.X, padx=5, pady=5)
        btn_accion = tk.Button(self.toolbar, text="Acción", command=lambda: self.controller.handle_add_node("accion"))
        btn_accion.pack(fill=tk.X, padx=5, pady=5)
        btn_final = tk.Button(self.toolbar, text="Final", command=lambda: self.controller.handle_add_node("final"))
        btn_final.pack(fill=tk.X, padx=5, pady=5)
        btn_condicional = tk.Button(self.toolbar, text="Condicional", command=lambda: self.controller.handle_add_node("condicional"))
        btn_condicional.pack(fill=tk.X, padx=5, pady=5)
        btn_multiples = tk.Button(self.toolbar, text="Múltiples Respuestas", command=lambda: self.controller.handle_add_node("multiples"))
        btn_multiples.pack(fill=tk.X, padx=5, pady=5)
        btn_llm = tk.Button(self.toolbar, text="LLM", command=lambda: self.controller.handle_add_node("llm"))
        btn_llm.pack(fill=tk.X, padx=5, pady=5)
        btn_python = tk.Button(self.toolbar, text="Python", command=lambda: self.controller.handle_add_node("python"))
        btn_python.pack(fill=tk.X, padx=5, pady=5)

        btn_connect = tk.Button(self.toolbar, text="🔗 Conectar Nodos", command=self.controller.handle_start_connection)
        btn_connect.pack(fill=tk.X, padx=5, pady=5)

        btn_delete_node = tk.Button(self.toolbar, text="🗑️ Eliminar Nodo", command=self.controller.handle_delete_node)
        btn_delete_node.pack(fill=tk.X, padx=5, pady=5)

        btn_delete_conn = tk.Button(self.toolbar, text="❌ Eliminar Conexión", command=self.controller.handle_start_delete_connection)
        btn_delete_conn.pack(fill=tk.X, padx=5, pady=5)

        btn_save = tk.Button(self.toolbar, text="💾 Guardar Flujo", command=self.controller.save_flow)
        btn_save.pack(fill=tk.X, padx=5, pady=5)

        btn_load = tk.Button(self.toolbar, text="📂 Cargar Flujo", command=self.controller.load_flow)
        btn_load.pack(fill=tk.X, padx=5, pady=5)

        btn_execute = tk.Button(self.toolbar, text="▶ Ejecutar Flujo", command=self.controller.handle_execute_flow)
        btn_execute.pack(fill=tk.X, padx=5, pady=5)
    
    def create_node_view(self, node):
        colors = {
            "inicio": "lightgreen",
            "final": "lightcoral",
            "accion": "lightblue",
            "condicional": "lightyellow",
            "multiples": "lightpink",
            "llm": "lightcyan",
            "python": "plum"
        }
        x, y = node.x, node.y
        display_text = f"{node.title}\n{node.text}" if node.title else node.text

        if node.node_type == "condicional":
            rect_id = self.canvas.create_rectangle(x, y, x+120, y+60,
                                                   fill=colors.get(node.node_type, "white"),
                                                   tags=(node.id, "node"))
            text_id = self.canvas.create_text(x+60, y+30, text=display_text, tags=(node.id, "node"))
            input_id = self.canvas.create_oval(x-5, y+25, x+5, y+35,
                                               fill="black",
                                               tags=(node.id, "connection_point", "input_point"))
            output_true = self.canvas.create_oval(x+115, y+10, x+125, y+20,
                                                  fill="black",
                                                  tags=(node.id, "connection_point", "output_true"))
            output_false = self.canvas.create_oval(x+115, y+40, x+125, y+50,
                                                   fill="black",
                                                   tags=(node.id, "connection_point", "output_false"))
            true_label = self.canvas.create_text(x+130, y+15, text="T", font=("Arial", 8), fill="green")
            false_label = self.canvas.create_text(x+130, y+45, text="F", font=("Arial", 8), fill="red")
            ids = {
                "rect": rect_id, "text": text_id, "input": input_id,
                "output_true": output_true, "output_false": output_false,
                "true_label": true_label, "false_label": false_label
            }
        elif node.node_type in ["multiples", "llm", "python"]:
            rect_id = self.canvas.create_rectangle(x, y, x+120, y+60,
                                                   fill=colors.get(node.node_type, "white"),
                                                   tags=(node.id, "node"))
            text_id = self.canvas.create_text(x+60, y+30, text=display_text, tags=(node.id, "node"))
            input_id = self.canvas.create_oval(x-5, y+25, x+5, y+35,
                                               fill="black",
                                               tags=(node.id, "connection_point", "input_point"))
            output_id = self.canvas.create_oval(x+115, y+25, x+125, y+35,
                                                fill="black",
                                                tags=(node.id, "connection_point", "output_point"))
            ids = {"rect": rect_id, "text": text_id, "input": input_id, "output": output_id}
        else:
            # inicio, accion, final
            rect_id = self.canvas.create_rectangle(x, y, x+100, y+50,
                                                   fill=colors.get(node.node_type, "white"),
                                                   tags=(node.id, "node"))
            text_id = self.canvas.create_text(x+50, y+25, text=display_text, tags=(node.id, "node"))
            input_id = self.canvas.create_oval(x-5, y+20, x+5, y+30,
                                               fill="black",
                                               tags=(node.id, "connection_point", "input_point"))
            output_id = self.canvas.create_oval(x+95, y+20, x+105, y+30,
                                                fill="black",
                                                tags=(node.id, "connection_point", "output_point"))
            ids = {"rect": rect_id, "text": text_id, "input": input_id, "output": output_id}

        return NodeView(node, self.canvas, ids)
    
    def update_node_view(self, node_view):
        node = node_view.node
        x, y = node.x, node.y
        display_text = f"{node.title}\n{node.text}" if node.title else node.text

        if node.node_type == "condicional":
            self.canvas.coords(node_view.ids["rect"], x, y, x+120, y+60)
            self.canvas.coords(node_view.ids["text"], x+60, y+30)
            self.canvas.itemconfig(node_view.ids["text"], text=display_text)
            self.canvas.coords(node_view.ids["input"], x-5, y+25, x+5, y+35)
            self.canvas.coords(node_view.ids["output_true"], x+115, y+10, x+125, y+20)
            self.canvas.coords(node_view.ids["output_false"], x+115, y+40, x+125, y+50)
            self.canvas.coords(node_view.ids["true_label"], x+130, y+15)
            self.canvas.coords(node_view.ids["false_label"], x+130, y+45)

        elif node.node_type in ["multiples", "llm", "python"]:
            self.canvas.coords(node_view.ids["rect"], x, y, x+120, y+60)
            self.canvas.coords(node_view.ids["text"], x+60, y+30)
            self.canvas.itemconfig(node_view.ids["text"], text=display_text)
            self.canvas.coords(node_view.ids["input"], x-5, y+25, x+5, y+35)
            self.canvas.coords(node_view.ids["output"], x+115, y+25, x+125, y+35)

        else:
            # inicio, accion, final
            self.canvas.coords(node_view.ids["rect"], x, y, x+100, y+50)
            self.canvas.coords(node_view.ids["text"], x+50, y+25)
            self.canvas.itemconfig(node_view.ids["text"], text=display_text)
            self.canvas.coords(node_view.ids["input"], x-5, y+20, x+5, y+30)
            self.canvas.coords(node_view.ids["output"], x+95, y+20, x+105, y+30)
    
    def delete_node_view(self, node_view):
        for item in node_view.ids.values():
            self.canvas.delete(item)
    
    def create_connection_view(self, start_node, end_node, branch="default"):
        if start_node.node_type == "condicional":
            if branch == "true":
                start_point = (start_node.x + 120, start_node.y + 15)
            else:
                start_point = (start_node.x + 120, start_node.y + 45)
        else:
            start_point = start_node.output_point
        end_point = end_node.input_point
        line_id = self.canvas.create_line(start_point[0], start_point[1],
                                          end_point[0], end_point[1],
                                          arrow=tk.LAST, tags="connection")
        return line_id
    
    def update_connection_view(self, connection_id, start_node, end_node, branch="default"):
        if start_node.node_type == "condicional":
            if branch == "true":
                start_point = (start_node.x + 120, start_node.y + 15)
            else:
                start_point = (start_node.x + 120, start_node.y + 45)
        else:
            start_point = start_node.output_point
        end_point = end_node.input_point
        self.canvas.coords(connection_id, start_point[0], start_point[1], end_point[0], end_point[1])
    
    def delete_connection_view(self, connection_id):
        self.canvas.delete(connection_id)
    
    def highlight_node_view(self, node_view):
        self.canvas.itemconfig(node_view.ids["rect"], outline="red", width=3)
    
    def unhighlight_node_view(self, node_view):
        self.canvas.itemconfig(node_view.ids["rect"], outline="black", width=1)
    
    def show_warning(self, message):
        messagebox.showwarning("Advertencia", message)
    
    def show_info(self, title, message):
        messagebox.showinfo(title, message)
    
    def mainloop(self):
        self.root.geometry("1200x700")
        self.root.mainloop()
