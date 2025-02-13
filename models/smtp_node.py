# models/smtp_node.py
from models.nodes import FlowNode
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tkinter import Toplevel, ttk
import tkinter as tk

class SmtpNode(FlowNode):
    def __init__(self, x, y):
        super().__init__(x, y, "smtp", "SMTP", "Enviar Correo")

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.title("Configurar Nodo SMTP")
        dialog.transient(parent)
        dialog.grab_set()

        # Campos de configuración
        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if self.title:
            entry_title.insert(0, self.title)

        lbl_server = ttk.Label(dialog, text="Servidor SMTP:")
        lbl_server.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entry_server = ttk.Entry(dialog, width=40)
        entry_server.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        lbl_port = ttk.Label(dialog, text="Puerto SMTP:")
        lbl_port.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_port = ttk.Entry(dialog, width=40)
        entry_port.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        lbl_user = ttk.Label(dialog, text="Usuario:")
        lbl_user.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_user = ttk.Entry(dialog, width=40)
        entry_user.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        lbl_pass = ttk.Label(dialog, text="Contraseña:")
        lbl_pass.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_pass = ttk.Entry(dialog, width=40, show="*")
        entry_pass.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        lbl_from = ttk.Label(dialog, text="Remitente:")
        lbl_from.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        entry_from = ttk.Entry(dialog, width=40)
        entry_from.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        lbl_to = ttk.Label(dialog, text="Destinatario:")
        lbl_to.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        entry_to = ttk.Entry(dialog, width=40)
        entry_to.grid(row=6, column=1, padx=10, pady=5, sticky="w")

        lbl_subject = ttk.Label(dialog, text="Asunto:")
        lbl_subject.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        entry_subject = ttk.Entry(dialog, width=40)
        entry_subject.grid(row=7, column=1, padx=10, pady=5, sticky="w")

        lbl_body = ttk.Label(dialog, text="Cuerpo del Correo:")
        lbl_body.grid(row=8, column=0, padx=10, pady=5, sticky="nw")
        txt_body = tk.Text(dialog, width=60, height=10)
        txt_body.grid(row=8, column=1, padx=10, pady=5, sticky="w")

        html_var = tk.BooleanVar()
        chk_html = ttk.Checkbutton(dialog, text="Contenido en HTML", variable=html_var)
        chk_html.grid(row=9, column=1, padx=10, pady=5, sticky="w")

        def on_ok():
            self.title = entry_title.get().strip()
            self.config["smtp_server"] = entry_server.get().strip()
            self.config["smtp_port"] = entry_port.get().strip()
            self.config["user"] = entry_user.get().strip()
            self.config["password"] = entry_pass.get().strip()
            self.config["from"] = entry_from.get().strip()
            self.config["to"] = entry_to.get().strip()
            self.config["subject"] = entry_subject.get().strip()
            self.config["body"] = txt_body.get("1.0", tk.END).strip()
            self.config["is_html"] = html_var.get()
            self.config["action_type"] = "smtp"
            self.text = f"SMTP: {self.config.get('subject', '')}" or "SMTP"
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=10, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=10, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)

    def execute(self, context):
        try:
            def resolve_text(text):
                # Reemplaza variables embebidas en el texto usando el contexto
                possibles = re.findall(r'\$\{([^}]+)\}', text)
                for var in possibles:
                    value = context.get(var, "")
                    text = text.replace(f"${{{var}}}", str(value))
                return text

            server = self.config.get("smtp_server", "")
            port = int(self.config.get("smtp_port", "0"))
            user = self.config.get("user", "")
            password = self.config.get("password", "")
            remitente = self.config.get("from", "")
            destinatario = self.config.get("to", "")
            subject = resolve_text(self.config.get("subject", ""))
            body = resolve_text(self.config.get("body", ""))
            is_html = self.config.get("is_html", False)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = remitente
            msg["To"] = destinatario
            mime_body = MIMEText(body, "html" if is_html else "plain")
            msg.attach(mime_body)

            smtp = smtplib.SMTP(server, port)
            smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(remitente, destinatario.split(","), msg.as_string())
            smtp.quit()
            print(f"Correo enviado exitosamente a {destinatario}")
        except Exception as e:
            print(f"Error al enviar correo SMTP: {str(e)}")
