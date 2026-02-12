import socket

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
            data, addr = self.sock.recvfrom(self.BUFFER_LEN)
            print(f"Received packet from {addr}:{data.decode()}")
            if data.decode().strip() == "exit":
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
            print(f"Send UDP packet to {self.UDP_IP}:{self.port}: {message}")
        except Exception:
            self.sock.close()
