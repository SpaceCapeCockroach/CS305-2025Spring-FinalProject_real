import json, time, threading
from utils import generate_message_id
from outbox import enqueue_message


known_peers = {}        # { peer_id: (ip, port) }
peer_flags = {}         # { peer_id: { 'nat': True/False, 'light': True/False } }
reachable_by = {}       # { peer_id: { set of peer_ids who can reach this peer }}
peer_config={}          
from peer_manager import peer_status
def is_reachable(self_id, target_id):
    self_nat = peer_config.get(self_id, {}).get('nat', False)
    target_nat = peer_config.get(target_id, {}).get('nat', False)
    self_network = peer_config.get(self_id, {}).get('localnetworkid',None)
    target_network = peer_config.get(target_id, {}).get('localnetworkid',None)
    
    # 非NAT节点可以访问任何非NAT节点
    if not self_nat and not target_nat:
        return True
    
    # 同一网络内的节点可以互相访问
    if self_network == target_network:
        return True
    
    return False
def start_peer_discovery(self_id, self_info):
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
                "fanout": peer_config.get(self_id, {}).get('fanout', 0),  # 可选字段，fanout值
                "localnetworkid": peer_config.get(self_id, {}).get('localnetworkid', None),
                "relay":self_id,
                "TTL": 3,  # 可选字段，TTL值
                "message_id": generate_message_id()
            }
            # self_network_id = peer_config.get(self_id, {}).get('localnetworkid', None)
            # 2. 发送给所有已知节点
            k_peers = known_peers.copy()  # 避免在迭代时修改字典
            for peer_id in k_peers:
                peer_ip, peer_port = known_peers[peer_id]
                if peer_id == self_id: continue  # 不发送给自己
                # if not is_reachable(self_id, peer_id):
                #     print(f"[debug]Peer {self_id} cannot reach {peer_id}, skipping hello message.")
                #     continue
                enqueue_message(
                    peer_id, peer_ip ,peer_port,json.dumps(message),
                )
                print(f"[{self_id}][debug]Sent hello message to {peer_id} at {peer_ip}:{peer_port}!!!!!!")
            time.sleep(20)
    threading.Thread(target=loop, daemon=True).start()

def handle_hello_message(msg, self_id):
    
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
        relay = data['relay']  # 可选字段
        fanout = data.get('fanout', 0)  # 可选字段
        data['relay'] = self_id  # 添加relay字段
        data['TTL']-=1


        if self_id == sender_id:
            return  # 不处理自己的HELLO消息
        

        if data['TTL'] > 0:
            for peer_id in known_peers:
                #将helo转发给所有的已知节点
                peer_ip, peer_port = known_peers[peer_id]
                if peer_id == sender_id or peer_id == self_id: continue  # 不发送给发送方,不给自己发
                enqueue_message(
                    peer_id, peer_ip ,peer_port,json.dumps(data),
                )
                print(f"[{self_id}][relay_hello]Relay hello message from sender:{sender_id} to {peer_id} at {peer_ip}:{peer_port}!!!!!!")
        
        # 2. 处理新节点
       
        peer_flags[sender_id] = flags
        if sender_id not in known_peers :
            # or (not peer_status.get(sender_id, 'UNKNOWN') == 'ALIVE')
            # 如果是新节点，或者之前的节点状态不是ALIVE    
            known_peers[sender_id] = (ip, port)
            peer_config[sender_id] = {
                "ip": ip,
                "port": port,
                "fanout": fanout,
                "nat": flags.get('nat', False),
                "light": flags.get('light', False),
                "localnetworkid": data.get('localnetworkid', None)
            }
            print(f"[{self_id}]New peer discovered: {sender_id}@{ip}:{port}")
        
        # 添加中间节点到reachable_by
        reachable_by.setdefault(sender_id, set()).add(relay)
        if not is_reachable(self_id, sender_id):
            print(f"receievd HELLO from {sender_id} (unreachable directly: sender_nat={flags.get('nat', True)}, self_nat={peer_flags[self_id]['nat']})")
            print(f"But , Peer {self_id} can reach {sender_id} through {relay}")
        else:
            # 如果可以到达，记录可达性，将sender_id添加到reachable_by
            reachable_by.setdefault(sender_id, set()).add(sender_id)
        

        # if flags.get('nat',False) or peer_config.get(self_id, {}).get('localnetworkid', None) == peer_config.get(sender_id, {}).get('localnetworkid', None):
        #     # 如果是NAT节点，并且在同一局域网内，记录可达性
        #     reachable_by.setdefault(sender_id, set()).add(sender_id)
        #     print(f"Peer {self_id} is NATed, reachable by {sender_id}")
    except KeyError as e:
        print(f"Invalid hello message: missing {e}")
    except json.JSONDecodeError:
        print("Failed to parse hello message")


