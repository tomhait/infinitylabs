from sockets import *

if __name__ == "__main__":
    print("Who you are?")
    print("Type 1 for server\nType 2 for client")
    my_type = input("> ").strip()
    if my_type == "1":
        server = MyUDPServer()
        server.start()
    elif my_type == "2":
        client = MyUDPClient()
        client.start()
    else:
        print("Wrong option, GoodBye!")
