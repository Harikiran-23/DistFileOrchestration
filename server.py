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
    usrs = {}
    with open("id_passwd.txt", 'r') as f:
        for line in f:
            u, p = line.strip().split(',')
            usrs[u] = p
    return usrs

def auth(u, p, usrs):
    if u in usrs and usrs[u] == p:
        print("Client exists and authenticated", u, p)
        return True
    else:
        return False

def h_client(conn, addr, usrs):
    try:
        u = conn.recv(1024).decode().strip()
        p = conn.recv(1024).decode().strip()

        if not auth(u, p, usrs):
            conn.sendall("0".encode())
            return

        conn.sendall(b"AUTH success")
        user_path = os.path.join("server_storage", u)

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
    finally:
        conn.close()

def h_up(conn, u_path):  
    if not os.path.exists(u_path):  
        os.makedirs(u_path)  

    f_name = conn.recv(1024).decode().strip()  
    f_path = os.path.join(u_path, f_name)  

    conn.sendall("File received".encode())  
    with open(f_path, 'wb') as f:  
        while True:  
            data = conn.recv(1024)  
            print(data)  
            if data == "END".encode():  
                break  
            f.write(data)  

    conn.sendall("File upload completed.\n".encode())

def h_down(conn, u_path):  
    filename = conn.recv(1024).decode().strip()  
    f_path = os.path.join(u_path, filename)  
    if os.path.exists(f_path):  
        conn.sendall("File Exists, Download will start now~\n".encode())  
        with open(f_path, 'rb') as f:  
            data = f.read(1024)  
            print(data)  
            print("============================================")  
            while data:  
                conn.sendall(data)  
                data = f.read(1024)  
                print(data)  
                print("============================================")  
            conn.sendall("END".encode())  
    else:  
        conn.sendall("File not found.\n".encode())

def h_list(conn, u_path):
    files = os.listdir(u_path)
    conn.sendall("\n".join(files).encode() + b"\n")

def h_view(conn, u_path):
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
    conn.sendall(b"Enter file name: ")
    filename = conn.recv(1024).decode().strip()
    f_p = os.path.join(u_path, filename)

    if os.path.exists(f_p):
        os.remove(f_p)
        conn.sendall(b"Deleted successfully\n")
    else:
        conn.sendall(b"File not found\n")


def signal_handler(sig, frame):
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