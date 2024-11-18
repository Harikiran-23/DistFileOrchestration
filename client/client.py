import socket
import os

# Server configuration
HOST = '127.0.0.1'  # Server IP address
PORT = 12345        # Server port

# Client functions for each command
def upload_file(client_socket):
    filename = input("Enter the filename to upload: ").strip()
    if not os.path.exists(filename):
        print("File does not exist.")
        return

    client_socket.sendall(b"UPLOAD")
    client_socket.sendall(filename.encode())
    print(client_socket.recv(1024).decode())  # Server acknowledgment

    with open(filename, 'rb') as f:
        data = f.read(1024)
        while data:
            client_socket.sendall(data)
            data = f.read(1024)
        client_socket.sendall(b"END")
    print(client_socket.recv(1024).decode())  # Confirmation message

def download_file(client_socket):
    filename = input("Enter the filename to download: ").strip()
    client_socket.sendall(b"DOWNLOAD")
    client_socket.sendall(filename.encode())

    response = client_socket.recv(1024)
    if response == b"File not found.\n":
        print(response.decode())
        return

    with open(filename, 'wb') as f:
        data = client_socket.recv(1024)
        while data != b"END":
            f.write(data)
            data = client_socket.recv(1024)

    print("File download completed.")

def list_files(client_socket):
    client_socket.sendall(b"LIST")
    print("Files on server:")
    print(client_socket.recv(1024).decode())

def view_file(client_socket):
    filename = input("Enter the filename to view: ").strip()
    client_socket.sendall(b"VIEW")
    client_socket.recv(1024)  # Wait for server's readiness
    client_socket.sendall(filename.encode())

    response = client_socket.recv(1024)
    if response == b"File not found\n":
        print(response.decode())
    else:
        print("File preview (first 1024 bytes):")
        print(response.decode())

def delete_file(client_socket):
    filename = input("Enter the filename to delete: ").strip()
    client_socket.sendall(b"DELETE")
    client_socket.recv(1024)  # Wait for server's readiness
    client_socket.sendall(filename.encode())
    print(client_socket.recv(1024).decode())  # Deletion confirmation

# Main client function
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        #Choose login or sign-up
        choice = input("Do you want to (1) Login or (2) Sign Up? Enter 1 or 2: ").strip()
        if choice == "2":
            client_socket.sendall(b"2")
            username = input("Enter a username: ").strip()
            client_socket.sendall(username.encode())
            password = input("Enter a password: ").strip()
            client_socket.sendall(password.encode())

            response = client_socket.recv(1024).decode()
            print(response)
            return

        elif choice == "1":
            client_socket.sendall(b"1")
            username = input("Username: ").strip()
            client_socket.sendall(username.encode())
            password = input("Password: ").strip()
            client_socket.sendall(password.encode())

            # Authentication response
            response = client_socket.recv(1024).decode()
            if response == "0":
                print("User does not exist. Closing connection.")
                return
            elif response == "-1":
                print("Invalid password!")
                return
            elif response == "AUTH success":
                print("Login successful!")

            #Command loop
            while True:
                command = input("Enter command (UPLOAD, DOWNLOAD, LIST, VIEW, DELETE, EXIT): ").strip().upper()
                if command == "UPLOAD":
                    upload_file(client_socket)
                elif command == "DOWNLOAD":
                    download_file(client_socket)
                elif command == "LIST":
                    list_files(client_socket)
                elif command == "VIEW":
                    view_file(client_socket)
                elif command == "DELETE":
                    delete_file(client_socket)
                elif command == "EXIT":
                    client_socket.sendall(b"EXIT")
                    print("Exiting...")
                    break
                else:
                    print("Invalid command.")
        else:
            print("Invalid choice. Closing connection.")
            return

main()