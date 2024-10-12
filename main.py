import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from server import HttpServer
import threading

class ServerManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("logiciel de qualité")
        self.geometry("1100x500")

        self.servers = {}

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.pack(side=ctk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side=ctk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_server_frame = ctk.CTkFrame(self.left_frame)
        self.create_server_frame.pack(fill=tk.X)

        ctk.CTkLabel(self.create_server_frame, text="Nom du serveur:").pack(anchor=tk.W)
        self.server_name_entry = ctk.CTkEntry(self.create_server_frame)
        self.server_name_entry.pack(fill=tk.X)

        ctk.CTkLabel(self.create_server_frame, text="Port du serveur:").pack(anchor=tk.W)
        self.server_port_entry = ctk.CTkEntry(self.create_server_frame)
        self.server_port_entry.pack(fill=tk.X)

        ctk.CTkLabel(self.create_server_frame, text="Dossier racine:").pack(anchor=tk.W)
        self.server_root_entry = ctk.CTkEntry(self.create_server_frame)
        self.server_root_entry.pack(fill=tk.X)

        self.browse_button = ctk.CTkButton(self.create_server_frame, text="Parcourir", command=self.browse_directory)
        self.browse_button.pack(pady=5)

        self.create_button = ctk.CTkButton(self.create_server_frame, text="Créer le serveur", command=self.create_server)
        self.create_button.pack(pady=10)

        self.server_listbox = tk.Listbox(self.left_frame)
        self.server_listbox.pack(fill=tk.BOTH, expand=True, pady=10)
        self.server_listbox.bind('<<ListboxSelect>>', self.display_server_info)

        self.server_info_text = ctk.CTkTextbox(self.right_frame, height=90, wrap=tk.WORD)
        self.server_info_text.pack(side=ctk.TOP, fill=tk.X)

        self.logs_label = ctk.CTkLabel(self.right_frame, text="Logs:")
        self.logs_label.pack(side=ctk.TOP, anchor=tk.W)

        self.logs_display_text = ctk.CTkTextbox(self.right_frame, height=10, wrap=tk.WORD)
        self.logs_display_text.pack(side=ctk.BOTTOM, fill=tk.BOTH, expand=True)

        self.delete_button = ctk.CTkButton(self.right_frame, text="Supprimer le serveur", command=self.delete_server)
        self.delete_button.pack(pady=10)

        self.after(1000, self.update_logs)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.server_root_entry.delete(0, tk.END)
            self.server_root_entry.insert(0, directory)

    def create_server(self):
        server_name = self.server_name_entry.get()
        server_port = self.server_port_entry.get()
        server_root = self.server_root_entry.get()

        self.server_name_entry.delete(0, ctk.END)
        self.server_port_entry.delete(0, ctk.END)
        self.server_root_entry.delete(0, ctk.END)
        if not server_name or not server_port or not server_root:
            messagebox.showwarning("Erreur", "Veuillez remplir tous les champs")
            return

        try:
            server_port = int(server_port)
        except ValueError:
            messagebox.showwarning("Erreur", "Le port doit être un nombre entier")
            return

        if server_name in self.servers:
            messagebox.showwarning("Erreur", "Un serveur avec ce nom existe déjà")
            return

        server = HttpServer(server_name, server_root, server_port)
        self.servers[server_name] = server
        self.server_listbox.insert(tk.END, server_name)

        threading.Thread(target=server.run, daemon=True).start()

    def display_server_info(self, event):
        selected_server = self.get_selected_server()
        if selected_server:
            self.server_info_text.delete(1.0, tk.END)
            info = (
                f"Nom du serveur: {selected_server.name}\n"
                f"Adresse: {selected_server.address}\n"
                f"Port: {selected_server.port}\n"
                f"Dossier racine: {selected_server.root}\n"
                f"Nombre de visites: {selected_server.nb_visites}\n"
            )
            self.server_info_text.insert(tk.END, info)

    def delete_server(self):
        selected_server = self.get_selected_server()
        if selected_server:
            server_name = selected_server.name
            selected_server.close_server()
            del self.servers[server_name]
            self.server_listbox.delete(self.server_listbox.curselection())
            self.logs_display_text.delete(1.0, tk.END)
            self.server_info_text.delete(1.0, tk.END)

    def get_selected_server(self) -> HttpServer | None:
        try:
            selected_index = self.server_listbox.curselection()[0]
            selected_name = self.server_listbox.get(selected_index)
            return self.servers[selected_name]
        except IndexError:
            return None

    def update_logs(self):
        selected_server = self.get_selected_server()
        if selected_server:
            self.logs_display_text.delete(1.0, tk.END)
            for log in selected_server.logs:
                self.logs_display_text.insert(tk.END, log + '\n')
            self.display_server_info(None)
        self.after(1000, self.update_logs)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    s = ServerManagerApp()
    s.mainloop()
