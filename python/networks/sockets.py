import os
import socket
import threading
import time
import select
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

__all__ = ("MyUDPServer", "MyUDPClient", "MyTCPServer",
           "MyTCPClient", "MyBroadcastServer", "MyBroadcastListener",
           "ReactorServer", "run_clients_simulation")
###########################################################################

class Server(ABC):
    @abstractmethod
    def start(self):
        pass

class Client(ABC):
    abstractmethod
    def start(self):
        pass

    abstractmethod
    def send_packet(self, message):
        pass

###########################################################################
###########################################################################
class MyUDPServer(Server):
    """
    UDP server
    """
    UDP_IP = os.getenv("UDP_IP")
    BUFFER_LEN = 1024

    def __init__(self, port_num = 5000):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        self.sock.bind((self.UDP_IP, self.port))
        print(f"Listening for UDP packets on {self.UDP_IP}:{self.port}")

        while True:
            try:
                data, addr = self.sock.recvfrom(self.BUFFER_LEN)
                print(f"Received packet from {addr}:{data.decode()}")
            except KeyboardInterrupt:
                print("\nClosing server")
                self.sock.close()
                break

class MyUDPClient(Client):
    """
    UDP client
    """
    UDP_IP = os.getenv("UDP_IP")
    BUFFER_LEN = 1024

    def __init__(self, port_num = 5000):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        print("Type \"exit\" to exit or your message to be sent")
        while True:
            message = input("> ")
            self.send_packet(message)
            if message == "exit":
                self.sock.close()
                break

    def send_packet(self, message = "Ping"):
        try:
            self.sock.sendto(message.encode(), (self.UDP_IP, self.port))
            print(f"Sent UDP packet to {self.UDP_IP}:{self.port}: {message}")
        except Exception:
            self.sock.close()

###########################################################################
###########################################################################
class MyTCPServer(Server):
    """
    TCP server
    """
    TCP_IP = os.getenv("TCP_IP")
    BUFFER_LEN = 1024
    totalclient = 10
    idle_limit = 60

    def __init__(self, port_num = 5005):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.TCP_IP, self.port))
        self.sock.listen(self.totalclient)
        print(f"Server started on {self.TCP_IP}:{self.port}")

    def handle_client(self, conn, addr):
        print(f"New connection: {addr} client")
        connected = True
        while connected:
            try:
                data = conn.recv(self.BUFFER_LEN).decode().strip()
                if data == "exit":
                    connected = False
                else:
                    print(f"[{addr}] {data}")
            except:
                connected = False
        conn.close()
        print(f"[DISCONNECTED] {addr} closed")

    def start(self):
        """
        Starts TCP server
        Handles up to 10 client in parallel using threading
        """
        self.sock.settimeout(self.idle_limit)
        print(f"Server will automatically shut down after {self.idle_limit}")
        try:
            while True:
                try:
                    conn, addr = self.sock.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.start()
                    print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
                    print("Resetting idle time")
                except socket.timeout:
                    print(f"No clients connected/responded for {self.idle_limit} seconds.")
                    break
        finally:
            self.sock.close()
            print("server socket will be closed after the last client closes connection")

class MyTCPClient(Client):
    """
    TCP client
    """
    TCP_IP = os.getenv("TCP_IP")
    BUFFER_LEN = 1024

    def __init__(self, port_num = 5005):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.TCP_IP, self.port))

    def start(self):
        print("Type \"exit\" to exit or your message to be sent")
        while True:
            message = input("> ")
            self.send_packet(message)
            if message == "exit":
                self.sock.close()
                break

    def send_packet(self, message = "Ping"):
        try:
            self.sock.send(message.encode())
            print(f"Sent TCP packet to {self.TCP_IP}:{self.port}: {message}")
        except Exception:
            self.sock.close()

###########################################################################
###########################################################################
class MyBroadcastServer(Server):
    UDP_IP = '<broadcast>'


    def __init__(self, port_num=5010):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broad_addr = (self.UDP_IP, self.port)
        print("Starting broadcast")

    def start(self, message = "Hello"):
        try:
            while True:
                self.sock.sendto(message.encode(), self.broad_addr)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nBroadcast stopped")
        finally:
            self.sock.close()

class MyBroadcastListener:
    BUFFER_LEN = 1024

    def __init__(self, port_num=5010):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('',self.port))

    def start(self):
        print("Listening tp broadcast...")
        print("Select Ctrl+C to close")
        while True:
            try:
                data, addr = self.sock.recvfrom(self.BUFFER_LEN)
                data = data.decode()
                print(f"Received message from {addr}")
                print(data)
            except KeyboardInterrupt:
                print("Closing Listener...")
                self.sock.close()
                break


###########################################################################
###########################################################################
class Reactor:
    def __init__(self):
        self.sock_dict = {'r':[],'w':[],'e':[]}
        self.funcs = {}
        self.is_run = False

    def subscribe(self, sock, mode, func):
        self.sock_dict[mode].append(sock)
        self.funcs[(sock, mode)] = func

    def unsubscribe(self, sock, mode):
        if mode in self.sock_dict and sock in self.sock_dict[mode]:
            self.sock_dict[mode].remove(sock)
        self.funcs.pop((sock, mode), None)

    def run(self):
        self.is_run = True
        print("Started Reactor...")
        while self.is_run:
            r_list = [s for s in self.sock_dict['r'] if s.fileno() != -1]
            w_list = [s for s in self.sock_dict['w'] if s.fileno() != -1]
            e_list = [s for s in self.sock_dict['e'] if s.fileno() != -1]
            r, w, e = select.select(r_list, w_list, e_list,1.0)
            for sock in r:
                if (sock, 'r') in self.funcs:
                    self.funcs[(sock,'r')](sock)
            for sock in w:
                if (sock, 'w') in self.funcs:
                    self.funcs[(sock,'w')](sock)
            for sock in e:
                if (sock, 'e') in self.funcs:
                    self.funcs[(sock,'e')](sock)

    def stop(self):
        self.is_run = False

class ReactorServer(Server):
    TCP_IP = os.getenv("TCP_IP")
    BUFFER_LEN = 1024
    totalclient = 10

    def __init__(self, port_num = 5015):
        self.port = port_num
        self.messages = {}
        self.reactor = Reactor()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((self.TCP_IP, self.port))
        self.sock.listen(self.totalclient)
        self.sock.setblocking(False)
        print(f"Server started on {self.TCP_IP}:{self.port}")

        self.reactor.subscribe(self.sock, 'r', self.handle_accept)

    def handle_accept(self, sock):
        conn = sock.accept()
        conn[0].setblocking(False)
        self.reactor.subscribe(conn[0], 'r', self.handle_read)
        self.reactor.subscribe(conn[0], 'e', self.handle_except)
        print(f"Accepted connection from {conn[1]}")

    def handle_read(self, sock):
        try:
            data = sock.recv(self.BUFFER_LEN)
            if data:
                data = data.decode().strip()
                print(f"Received message: {data}")
                self.messages.setdefault(sock, []).append(data)
                self.reactor.subscribe(sock, 'w', self.handle_write)
            else:
                self.close_sock(sock)
        except ConnectionResetError:
            self.close_sock(sock)

    def handle_write(self, sock):
        if sock in self.messages:
            msg = self.messages[sock].pop(0)
            try:
                sock.send(msg.encode())
                if not self.messages[sock]:
                    del self.messages[sock]
            except ConnectionResetError:
                self.close_sock(sock)
        else:
            self.reactor.unsubscribe(sock, 'w')

    def handle_except(self, sock):
        print(f"Exception occurred: {sock.getpeername()}")
        self.close_sock(sock)

    def close_sock(self, sock):
        for mode in 'rwe':
            self.reactor.unsubscribe(sock,mode)

        self.messages.pop(sock, None)

        try:
            sock.close()
        except:
            pass
        print("Closed a socket connection")

    def start(self):
        try:
            self.reactor.run()
        except KeyboardInterrupt:
            print("Closing Reactor Server")
            self.reactor.stop()
            self.sock.close()

BUFFER_LEN = 1024
totalclient = 10
def _client_simulate(idx):
    host = '127.0.0.1'
    port = 5015
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        msg = f"Hola, this is Client: {idx}"
        print(f"Client {idx} is sending: {msg}")
        sock.send(msg.encode())
        data = sock.recv(BUFFER_LEN).decode().strip()
        print(f"Client {idx} received: {data}")
        time.sleep(2)
        sock.send("Bye".encode())
        sock.close()
    except Exception as e:
        print(f"Client {idx} error: {e}")

def run_clients_simulation():
    threads = []
    print(f"Reactor test with {totalclient} clients")
    for i in range(totalclient):
        t = threading.Thread(target=_client_simulate, args=(i+1,))
        threads.append(t)
        t.start()
        time.sleep(0.2)

    for t in threads:
        t.join()
    print("ALL CLIENTS DONE")

