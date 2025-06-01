import socket
import threading
import time
import json
from message_handler import dispatch_message

RECV_BUFFER = 4096

def start_socket_server(self_id, self_ip, port):

    def listen_loop():
        # TODO: Create a TCP socket and bind it to the peer’s IP address and port.

        # TODO: Start listening on the socket for receiving incoming messages.

        # TODO: When receiving messages, pass the messages to the function `dispatch_message` in `message_handler.py`.

        # pass
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self_ip, port)
        server_socket.bind(server_address)
        server_socket.listen(20)  # 允许最大等待连接数
        print(f"TCP server started on {self_ip}:{port}")
        while True: 
            # 接受新连接
            client_socket, client_addr = server_socket.accept()
            print(f"New connection from {client_addr}")
            # 为每个连接创建新线程处理
            threading.Thread(
                target=handle_client,
                args=(client_socket, self_id, self_ip),
                daemon=True
            ).start()

    def handle_client(client_socket, self_id, self_ip):
        buffer = b''  # 用于累积数据
        try:
            while True:  # ← 新增接收循环
                data = client_socket.recv(RECV_BUFFER)
                if not data:  # 客户端正常关闭连接
                    print("Transmission by client completed ")
                    break
                buffer += data
                #print(f"raw_msg:{data}\n")
            try:
                if buffer:                    
                    threading.Thread(target=dispatch_message,args=(buffer.decode(), self_id, self_ip), daemon=True).start()
            except Exception as e:
                print(f"Error handling client: {e}")
        except ConnectionResetError:
            print("Client forcibly closed connection")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    # ✅ Run listener in background
    threading.Thread(target=listen_loop, daemon=True).start()

