import socket
import threading
import jpysocket
import json
from rich.console import Console
from rich.theme import Theme
import datetime

ctheme = Theme({
    "good" : "bold green",
    "error" : "bold white on dark_red",
    "warning": "bold white on light_goldenrod3",
    "info": "bold deep_sky_blue4",
    "disconnected": "bold dark_goldenrod",
    "connected": "bold yellow4",
    "establishingConnection": "bold grey53",
    "cmd": "bold gold1"
})

console = Console(theme=ctheme)
maxPlayers = 4300

class Server:
    global maxPlayers
    version = "0.1-DAHLIA"
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.players = []
        self.countries = []
        self.activeScenario = -1
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(maxPlayers+1)
        self.commands = ["players: lists all of the player ID's", "op [ID]: gives the specified player host benefits"]

    def log(self, tekst):
        console.print(datetime.datetime.now().strftime("[%H:%M:%S] ")+tekst)

    def printCommands(self):
        for x in self.commands:
            console.print("[[cmd]INFO[/cmd]] "+x)

    def broadcastToSender(self, message, sender):
        for client_socket in self.clients:
            if client_socket == sender:
                try:
                    client_socket.send(jpysocket.jpyencode(message))
                except OSError:
                    self.log(f"[error]ERROR[/error] Could not sync up with {sender}")

    def broadcast(self, message, sender):
        for client_socket in self.clients:
            if client_socket != sender:
                try:
                    client_socket.send(jpysocket.jpyencode(message))
                except OSError:
                    self.log("[error]ERROR[/error] Could not sync up with all of the players")

    def handle_client(self, client_socket, client_address):
        self.log(f"[establishingConnection]A new player with an ID of {client_address[1]} is trying to connect[/establishingConnection]")
        self.clients[client_socket] = client_address
        self.players.append(client_address[1])
        while True:
            try:
                try:
                    message = jpysocket.jpydecode(client_socket.recv(1024))
                    print(message)
                except ConnectionResetError: 
                    raise Exception
                if message:
                    match message:
                        case "disconnected":
                            raise Exception
                        case "player connected":
                            self.broadcastToSender(str("i"+str(client_address[1])), client_socket)
                            if self.activeScenario == -1:
                                pass
                            else:
                                self.broadcastToSender(str("s"+str(self.activeScenario)), client_socket)
                            try:
                                self.broadcast(str("p"+str(len(self.players))), client_socket)
                                self.log(f"[connected]Player {client_address[1]} connected[/connected]")
                            except ConnectionResetError: self.log("[error]ERROR[/error] Couldn't accept the player's connection")
                        case _:
                            match message[0:2]:
                                case "se":
                                    id = message.replace("se", "")
                                    if int(id) in self.countries:
                                        self.broadcastToSender("r", client_socket)
                                    else:
                                        self.broadcastToSender("e", client_socket)
                                        self.countries.append(int(id))
                                    return
                                case "sr":
                                    id = message.replace("sr", "")
                                    try:
                                        self.countries.remove(int(id))
                                    except: self.log(f"[warning]WARNING[/warning] Player {client_address[1]} selected a country and it became active")
                                    return
                            match message[0:1]:
                                case "s":
                                    id = message.replace("s", "")
                                    self.activeScenario = int(id)
                                    self.broadcast(str("s"+str(id)), client_socket)
                else:
                    raise Exception("AoC")
            except Exception:
                try:
                    self.players.remove(client_address[1])
                except: self.log("[error]ERROR[/error] Players connection was forcibly closed")
                del self.clients[client_socket]
                self.log(f"[disconnected]Player {client_address[1]} disconnected[/disconnected]")
                self.broadcast(str("p"+str(len(self.players)+1)), client_socket)
                client_socket.close()
                self.run()
                break

    def consoleHandler(self):
        msg = input("")
        match msg[0:2]:
            case "he": #help
                self.printCommands()
            case "pl": #players
                print(self.players)
            case "op": #op
                id = msg.replace("op", "")
                if id == "" or id not in(self.players): 
                    print("Unkown ID given")
                    server.consoleHandler()
                self.messages.append(str(f"o{id}"))
                print(f"Player with the ID{id} has been given host benefits")
        server.consoleHandler()

    def run(self):
        console_thread = threading.Thread(target=self.consoleHandler, args=())
        console_thread.start()
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

if __name__ == "__main__":
    port = 4445
    #ip = socket.gethostbyname(socket.gethostname())
    ip = "172.16.0.2"
    try:
        with open('config.aohmp') as file:
            data = file.read()
        json_data = json.loads(data)
        port = json_data["port"]
        maxPlayers = json_data["players"]
        server = Server(ip, port)
        if port <= 1024 or port > 65535:
            console.print('[warning]PORT has to be between numbers 1024 and 65535! Running on default PORT 44445.[/warning]')
            port = 44445
        if maxPlayers <= 1 or maxPlayers > 4300:
            console.print("[warning]WARNING[/warning] Number of players has to be between numbers 2 and 4300! Setting the number of players to default (4300).")
            maxPlayers = 4300
        console.print(f'Server running on version: [info]{Server.version}[/info]\nServer running on IP: [info]{ip}[/info] and PORT: [info]{port}[/info]\nMax number of players: [info]{maxPlayers}[/info]\nType [info]"help"[/info] in the console for all of the commands')
        server.run()
    except FileNotFoundError: print("Configuration file [config.aohmp] has not been found")