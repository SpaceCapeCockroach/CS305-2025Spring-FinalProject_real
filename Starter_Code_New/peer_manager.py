import threading
import time
import json
from collections import defaultdict
from utils import generate_message_id


peer_status = {} # {peer_id: 'ALIVE', 'UNREACHABLE' or 'UNKNOWN'}
last_ping_time = {} # {peer_id: timestamp}
rtt_tracker = {} # {peer_id: transmission latency}
Lock = threading.Lock()
# === Check if peers are alive ===

def start_ping_loop(self_id, peer_table):
    from outbox import enqueue_message
    def loop():
       # TODO: Define the JSON format of a `ping` message, which should include `{message typy, sender's ID, timestamp}`.

       # TODO: Send a `ping` message to each known peer periodically.
    #    pass
        PING_INTERVAL = 20  # 每60秒发送一次PING
        
        while True:
            # 1. 生成PING消息
            ping_msg = {
                "type": "PING",
                "sender": self_id,
                "timestamp": time.time(),
                "message_id": generate_message_id()
            }
            
            # 2. 发送给所有已知节点（排除黑名单）
            p_table =  peer_table.copy()  # 避免在迭代时修改字典
            for peer_id, (ip, port) in p_table.items():
                if peer_id not in blacklist and peer_id != self_id:
                    time.sleep(0.02)  # 添加间隔，避免同时发送
                    print(f"[{self_id}]发送 PING 消息到 {peer_id} ({ip}:{port})")
                    enqueue_message(
                        peer_id,ip, port,
                        json.dumps(ping_msg),
                    )
                   
            
            time.sleep(PING_INTERVAL)

    threading.Thread(target=loop, daemon=True).start()

def create_pong(sender, recv_ts):
    # TODO: Create the JSON format of a `pong` message, which should include `{message type, sender's ID, timestamp in the received ping message}`.
    # pass
    #"""创建PONG响应消息"""
    return {
        "type": "PONG",
        "sender": sender,
        "timestamp": recv_ts,
        "message_id": generate_message_id()
    }

def handle_pong(msg):
    # TODO: Read the information in the received `pong` message.

    # TODO: Update the transmission latenty between the peer and the sender (`rtt_tracker`).
    # pass
    # """处理PONG响应"""
    try:
        data = json.loads(msg)
        peer_id = data['sender']
        original_ts = data['timestamp']
      
        # 计算往返时间（RTT）
        rtt = (time.time() - original_ts) * 1000  # 转换为毫秒  
        print(f'收到来自 {peer_id} 的 PONG 响应，原始时间戳: {original_ts}, RTT: {rtt/1000:.2f} s')
        with Lock:
            # rtt_tracker[peer_id].append(rtt)
            rtt_tracker.setdefault(peer_id, []).append(rtt)
            print(f'更新RTT from {peer_id}: {rtt_tracker[peer_id]} ms')
        
            # 更新最后活跃时间
            # update_peer_heartbeat(peer_id)
        
            # 维护最近5次RTT样本
            if len(rtt_tracker[peer_id]) > 5:
                rtt_tracker[peer_id].pop(0)
            
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Invalid pong message: {e}")


def start_peer_monitor(self_id):
    import threading
    def loop():
        # TODO: Check the latest time to receive `ping` or `pong` message from each peer in `last_ping_time`.

        # TODO: If the latest time is earlier than the limit, mark the peer's status in `peer_status` as `UNREACHABLE` or otherwise `ALIVE`.
        TIMEOUT = 300  # 5分钟无响应视为离线
        peer_status[self_id] = 'MYSELF'# 自己的状态始终是 ALIVE
        while True:
            current_time = time.time()
            
            for peer_id, last_ts in list(last_ping_time.items()):
                # 跳过黑名单节点
                with Lock:
                    if peer_id in blacklist:
                        continue
                
                    # 计算离线时间
                    if current_time - last_ts > TIMEOUT:
                        peer_status[peer_id] = 'UNREACHABLE'
                    else:
                        peer_status[peer_id] = 'ALIVE'
            
            time.sleep(30)  # 每30秒检查一次
        # pass
    threading.Thread(target=loop, daemon=True).start()

def update_peer_heartbeat(peer_id):
    # TODO: Update the `last_ping_time` of a peer when receiving its `ping` or `pong` message.
    # pass
    last_ping_time[peer_id] = time.time()
    peer_status[peer_id] = 'ALIVE'
    print(f'更新 {peer_id} 的心跳状态为 ALIVE，时间戳: {last_ping_time[peer_id]}')


# === Blacklist Logic ===

blacklist = set() # The set of banned peers

peer_offense_counts = {} # The offence times of peers

def record_offense(peer_id):
    # TODO: Record the offence times of a peer when malicious behaviors are detected.

    # TODO: Add a peer to `blacklist` if its offence times exceed 3. 

    # pass
    MAX_OFFENSES = 3
    
    peer_offense_counts[peer_id] += 1
    print(f"Peer {peer_id} offense count: {peer_offense_counts[peer_id]}")
    
    if peer_offense_counts[peer_id] >= MAX_OFFENSES:
        with Lock:
            blacklist.add(peer_id)
            print(f"Added {peer_id} to blacklist")
        
            # 清除相关状态
            peer_status.pop(peer_id, None)
            last_ping_time.pop(peer_id, None)
            rtt_tracker.pop(peer_id, None)

