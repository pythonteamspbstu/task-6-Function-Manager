import socket
import sys

def main():
    host = '127.0.0.1'
    port = 8888

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Connected to CLI server at {host}:{port}")
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
        sys.exit(1)

    try:
        while True:
            data = s.recv(4096).decode()
            if not data:
                break
            
            print(data, end='')

            if data.endswith(': ') or 'Select option: ' in data:
                user_input = input()
                s.sendall((user_input + "\n").encode())
                
                if user_input.strip() == '7' and 'Select option: ' in data:
                    break
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        s.close()

if __name__ == "__main__":
    main()

