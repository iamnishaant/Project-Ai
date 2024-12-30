import socket
import threading
import os

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("192.168.131.2", 5555))

    # Function to receive and display the grid
    #N
    def receive_grid():
        while True:
            try:
                data = client.recv(4096).decode()
                if data:
                    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the terminal
                    print(data)
                else:
                    break
            except:
                break

    # Thread for receiving grid updates
    threading.Thread(target=receive_grid, daemon=True).start()

    # Send user input to the server
    #A
    while True:
        try:
            move = input("Move (W/A/S/D or EXIT to quit): ").strip().upper()
            if move in ["W", "A", "S", "D", "EXIT"]:
                client.sendall(move.encode())
                if move == "EXIT":
                    break
        except:
            break

    client.close()

if __name__ == "__main__":
    start_client()
