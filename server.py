import socket
import threading
import os
import signal
import sys

HOST = '127.0.0.1'
PORT = 12345

storage = "server_storage"
os.makedirs(storage, exist_ok=True)

def load_usrs():
    """Load users from the credentials file."""
    usrs = {}
    with open("id_passwd.txt", 'r') as f:
        for line in f:
            u, p = line.strip().split(',')
            usrs[u] = p
    return usrs

def auth(u, p, usrs):
    """Authenticate user based on provided credentials."""
    if u in usrs and usrs[u] == p:
        print("Client exists and authenticated", u, p)
        return 1
    elif u in usrs:
        print('Invalid password')
        return -1
    else:
        return 0

def signup_user(conn,usrs):
    """Handle the new user sign-up process."""
    u = conn.recv(1024).decode().strip()
    p = conn.recv(1024).decode().strip()

    # Check if the username already exists
    if u in usrs:
        conn.sendall(b"Username already exists. Please try a different one.\n")
        return False

    # Add new user to the credentials file
    with open("id_passwd.txt", 'a') as f:
        f.write(f"{u},{p}\n")
    usrs[u]=p
    # Create the user's directory
    user_path = os.path.join(storage, u)
    os.makedirs(user_path, exist_ok=True)

    conn.sendall(b"Sign-up successful.\n")
    print(f"New user signed up: {u}")
    return True

def h_client(conn, addr, usrs):
    """Handle client operations."""
    try:
        choice = conn.recv(1024).decode().strip()

        if choice == "2":
            if signup_user(conn, usrs):
                conn.sendall(b"Please restart the connection to log in.\n")
            return  # Disconnect

        elif choice == "1":
            conn.sendall(b"Enter username: ")
            u = conn.recv(1024).decode().strip()
            conn.sendall(b"Enter password: ")
            p = conn.recv(1024).decode().strip()

            auth_res = auth(u, p, usrs)
            if auth_res == 0:
                conn.sendall(b"0")  # User does not exist
                return
            elif auth_res == -1:
                conn.sendall(b"-1")  # Invalid password
                return

            conn.sendall(b"AUTH success")
            user_path = os.path.join(storage, u)

            while True:
                command = conn.recv(1024).decode().strip().upper()
                print(command)
                if command == "UPLOAD":
                    h_up(conn, user_path)
                elif command == "DOWNLOAD":
                    h_down(conn, user_path)
                elif command == "LIST":
                    h_list(conn, user_path)
                elif command == "VIEW":
                    h_view(conn, user_path)
                elif command == "DELETE":
                    h_del(conn, user_path)
                elif command == "EXIT":
                    break
                else:
                    conn.sendall(b"Invalid command.\n")
        else:
            conn.sendall(b"Invalid option. Disconnecting.\n")

    finally:
        conn.close()

def h_up(conn, u_path):  
    """Handle file upload from client."""
    if not os.path.exists(u_path):  
        os.makedirs(u_path)  

    f_name = conn.recv(1024).decode().strip()  
    f_path = os.path.join(u_path, f_name)  

    conn.sendall(b"File received")  
    with open(f_path, 'wb') as f:  
        while True:  
            data = conn.recv(1024)  
            if data == b"END":  
                break  
            f.write(data)  

    conn.sendall(b"File upload completed.\n")

def h_down(conn, u_path):  
    """Handle file download for client."""
    filename = conn.recv(1024).decode().strip()  
    f_path = os.path.join(u_path, filename)  
    if os.path.exists(f_path):  
        conn.sendall(b"File Exists, Download will start now~\n")  
        with open(f_path, 'rb') as f:  
            data = f.read(1024)  
            while data:  
                conn.sendall(data)  
                data = f.read(1024)  
            conn.sendall(b"END")  
    else:  
        conn.sendall(b"File not found.\n")

def h_list(conn, u_path):
    """List files in the user's directory."""
    files = os.listdir(u_path)
    conn.sendall("\n".join(files).encode() + b"\n")

def h_view(conn, u_path):
    """Preview the first 1024 bytes of a file."""
    conn.sendall(b"Enter file name: ")
    filename = conn.recv(1024).decode().strip()
    f_p = os.path.join(u_path, filename)

    if os.path.exists(f_p):
        with open(f_p, 'rb') as f:
            data = f.read(1024)
        conn.sendall(data + b"\n")
    else:
        conn.sendall(b"File not found\n")

def h_del(conn, u_path):
    """Delete a file from the user's directory."""
    conn.sendall(b"Enter file name: ")
    filename = conn.recv(1024).decode().strip()
    f_p = os.path.join(u_path, filename)

    if os.path.exists(f_p):
        os.remove(f_p)
        conn.sendall(b"Deleted successfully\n")
    else:
        conn.sendall(b"File not found\n")

def signal_handler(sig, frame):
    """Handle server shutdown gracefully."""
    print("\nServer shutting down gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Server is listening")

    while True:
        conn, addr = s.accept()
        print("Connection established", addr)
        c_thread = threading.Thread(target=h_client, args=(conn, addr, load_usrs()))
        c_thread.start()
