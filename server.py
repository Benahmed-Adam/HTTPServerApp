import socket
import os
from pathlib import Path
import datetime
import threading
from datetime import datetime

class HttpServer:

    def __init__(self, name: str, root: str, port: int) -> None:
        self.nb_visites = 0
        self.root = os.path.abspath(root)
        self.name = name
        self.logs = []
        self.port = port
        self.see_files = False
        self.lock = threading.Lock()

        self.add_log("Initialisation du serveur...")
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.add_log(f"Recherche des éléments dans le dossier {root}")
        self.pages = self.recherche_elements(root)
        self.add_log("Recherche finie, voici les éléments trouvés : " + ", ".join(self.pages))

    def close_server(self):
        self.add_log("Fermeture du serveur...")
        self.socket.close()
    
    def add_log(self, message : str):
        with self.lock:
            self.logs.insert(0,f"[{datetime.now().strftime('%H:%M:%S')}] : {message}")
    
    def add_visite(self):
        with self.lock:
            self.nb_visites += 1

    def recherche_elements(self, directory):
        elements = set()
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = Path(os.path.join(root, file))
                relative_path = filepath.relative_to(directory).as_posix()
                elements.add(relative_path)
        return elements
    
    def client_manager(self, client: tuple[socket.socket, str]):
        self.add_visite()
        client_socket, adresse = client
        try:
            data = client_socket.recv(32768).decode()
            if not data:
                client_socket.close()
                return
            
            filename = data.split()[1][1:] or "index.html"
            request_type = data.split()[0]
            self.add_log(f"Demande de l'element : '{filename}' venant de : {adresse}")
            response = b""
            if request_type == "GET":
                if filename in self.pages or filename == "index.html":
                    with open(os.path.join(self.root, filename), 'rb') as file:
                        response += file.read()
                    client_socket.send("HTTP/1.1 200 OK\r\n\r\n".encode())
                    client_socket.sendall(response)
                elif filename == "filesinfo" and self.see_files:
                    for content in self.pages:
                        response += f"{content}\n".encode()
                    client_socket.send("HTTP/1.1 200 OK\r\n\r\n".encode())
                    client_socket.sendall(response)
                else:
                    response += """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Erreur 404</title></head><body><h1>La page n'existe pas</h1></body></html>""".encode()
                    client_socket.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
                    client_socket.sendall(response)
            elif request_type == "POST":
                client_socket.send("HTTP/1.1 501 Not Implemented\r\n\r\n".encode())
            else:
                pass
        except Exception as e:
            self.add_log(f"Erreur : {str(e)}")
        finally:
            client_socket.close()

    def run(self):
        try:
            server_ip = socket.getaddrinfo(socket.gethostname(),self.port, socket.AF_INET6)[-1][-1][0]
            self.address = f"http://[{server_ip}]:{self.port}/"
            self.socket.bind((server_ip, self.port))
            self.socket.listen()
            self.add_log(f"Le serveur est prêt sur {self.address}")

            while True:
                client = self.socket.accept()
                self.pages = self.recherche_elements(self.root)
                threading.Thread(target=self.client_manager, args=(client,)).start()
        except Exception as e:
            self.add_log(f"Erreur : {str(e)}")
        finally:
            self.close_server()