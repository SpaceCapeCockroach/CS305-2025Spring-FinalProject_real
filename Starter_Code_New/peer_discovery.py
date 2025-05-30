import json, time, threading
from utils import generate_message_id


known_peers = {}        # { peer_id: (ip, port) }
peer_flags = {}         # { peer_id: { 'nat': True/False, 'light': True/False } }
reachable_by = {}       # { peer_id: { set of peer_ids who can reach this peer }}
peer_config={}          

def is_reachable(self_id, target_id):
    self_nat = peer_flags.get(self_id, {}).get('nat', False)
    target_nat = peer_flags.get(target_id, {}).get('nat', False)
    self_network = peer_config.get(self_id, {}).get('localnetworkid')
    target_network = peer_config.get(target_id, {}).get('localnetworkid')
    
    # 非NAT节点可以访问任何节点
    if not self_nat:
        return True
    
    # NAT节点只能访问同一网络的节点
    if self_nat and target_nat and self_network == target_network:
        return True
    
    return False
def start_peer_discovery(self_id, self_info):
    from outbox import enqueue_message
    def loop():
        # TODO: Define the JSON format of a `hello` message, which should include: `{message type, sender’s ID, IP address, port, flags, and message ID}`. 
        # A `sender’s ID` can be `peer_port`. 
        # The `flags` should indicate whether the peer is `NATed or non-NATed`, and `full or lightweight`. 
        # The `message ID` can be a random number.

        # TODO: Send a `hello` message to all known peers and put the messages into the outbox queue.
        # Tips: A NATed peer can only say hello to peers in the same local network. 
        #       If a peer and a NATed peer are not in the same local network, they cannot say hello to each other.
        # pass
        # 1. 构造hello消息
        while True:
            message = {
                "type": "HELLO",
                "sender": self_id,
                "ip": self_info['ip'],
                "port": self_info['port'],
                "flags": {
                    "nat": peer_flags.get(self_id ,{}).get('nat', False),
                    "light": peer_flags.get(self_id ,{}).get('light', False)
                },
                "message_id": generate_message_id()
            }
            self_network_id=peer_config.get(self_id, {}).get('localnetworkid', None)
            # 2. 发送给所有已知节点
            k_peers = known_peers.copy()  # 避免在迭代时修改字典
            for peer_id in k_peers:
                peer_ip, peer_port = known_peers[peer_id]
                if peer_id == self_id: continue  # 不发送给自己
                if not is_reachable(self_id, peer_id):
                    print(f"[debug]Peer {self_id} cannot reach {peer_id}, skipping hello message.")
                    continue
                enqueue_message(
                    peer_id, peer_ip ,peer_port,json.dumps(message),
                )
                print(f"[debug]Sent hello message to {peer_id} at {peer_ip}:{peer_port}!!!!!!")
            time.sleep(20)
    threading.Thread(target=loop, daemon=True).start()

def handle_hello_message(msg, self_id):
    new_peers = []
    
    # TODO: Read information in the received `hello` message.
     
    # TODO: If the sender is unknown, add it to the list of known peers (`known_peer`) and record their flags (`peer_flags`).
     
    # TODO: Update the set of reachable peers (`reachable_by`).

    # pass
    try:
        # 1. 解析消息
        data = json.loads(msg)
        sender_id = data['sender']  # 强制类型统一
        ip = data['ip']
        port = data['port']
        flags = data['flags']
        
        # 2. 处理新节点
        if not is_reachable(sender_id, self_id):
            print(f"Blocked HELLO from {sender_id} (unreachable: sender_nat={flags.get('nat', True)}, self_nat={peer_flags[self_id]['nat']})")
            return []
       
        peer_flags[sender_id] = flags
        if sender_id not in known_peers:    
            new_peers.append(sender_id) 
            known_peers[sender_id] = (ip, port)
            print(f"New peer discovered: {sender_id}@{ip}:{port}")
        # 3. 更新可达性
        if sender_id== self_id:
            print(f"Received hello message from self: {self_id}")
            return new_peers
        reachable_by.setdefault(self_id, set()).add(sender_id)
        if flags.get('nat',False):
            reachable_by.setdefault(sender_id, set()).add(self_id)
            print(f"Peer {self_id} is NATed, reachable by {sender_id}")
    except KeyError as e:
        print(f"Invalid hello message: missing {e}")
    except json.JSONDecodeError:
        print("Failed to parse hello message")

    return new_peers 


