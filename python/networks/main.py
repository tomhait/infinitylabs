from sockets import *

if __name__ == "__main__":
    con_type = input("TCP or UDP? ").strip()
    if con_type == "UDP":
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
    elif con_type == "TCP":
        print("Who you are?")
        print("Type 1 for server\nType 2 for client")
        my_type = input("> ").strip()
        if my_type == "1":
            server = MyTCPServer()
            server.start()
        elif my_type == "2":
            client = MyTCPClient()
            client.start()
        else:
            print("Wrong option, GoodBye!")
    else:
        print("Wrong option, GoodBye!")

