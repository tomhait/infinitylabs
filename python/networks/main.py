from sockets import *

if __name__ == "__main__":
    con_type = input("TCP or UDP, Broadcast or Reactor? ").strip()
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
    elif con_type == "Broadcast":
        print("Who you are?")
        print("Type 1 for Broadcaster\nType 2 for Listener")
        my_type = input("> ").strip()
        if my_type == "1":
            server = MyBroadcastServer()
            server.start()
        elif my_type == "2":
            client = MyBroadcastListener()
            client.start()
        else:
            print("Wrong option, GoodBye!")
    elif con_type == "Reactor":
        print("Who you are?")
        print("Type 1 for Reactor server\nType 2 for Client")
        my_type = input("> ").strip()
        if my_type == "1":
            server = ReactorServer()
            server.start()
        elif my_type == "2":
            run_clients_simulation()
        else:
            print("Wrong option, GoodBye!")
    else:
        print("Wrong option, GoodBye!")

