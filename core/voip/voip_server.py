import socket

def start_voip_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5060))
    server.listen(5)
    print("VOIP Server running on port 5060...")
    while True:
        conn, addr = server.accept()
        print(f"Connection from {addr}")
        conn.send(b'VOIP service ready\n')
        conn.close()

if __name__ == "__main__":
    start_voip_server()
