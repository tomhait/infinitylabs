import socket
import threading
import time

class MyUDPServer:
    UDP_IP = "127.0.0.1"
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

class MyUDPClient:
    UDP_IP = "127.0.0.1"
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

class MyTCPServer:
    TCP_IP = "127.0.0.1"
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

class MyTCPClient:
    TCP_IP = "127.0.0.1"
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

class MyBroadcastServer:
    UDP_IP = '<broadcast>'


    def __init__(self, port_num=5010):
        self.port = port_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broad_addr = (self.UDP_IP, self.port)
        print("Starting broadcast")

    def send_message(self, message = "Hello"):
        try:
            while True:
                self.sock.sendto(message.encode(), self.broad_addr)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nBroadcast stopped")
        finally:
            self.sock.close()

class MyBroadcastListener:
    pass