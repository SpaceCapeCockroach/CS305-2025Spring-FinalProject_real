import socket
import threading
import time
import json
import random
from collections import defaultdict, deque
from threading import Lock
from utils import generate_message_id

# === Per-peer Rate Limiting ===
RATE_LIMIT = 50  # max messages
TIME_WINDOW = 10  # per seconds
peer_send_timestamps = defaultdict(list) # the timestamps of sending messages to each peer

MAX_RETRIES = 3
RETRY_INTERVAL = 1  # seconds
QUEUE_LIMIT = 50

# Priority levels
PRIORITY_HIGH = {"PING", "PONG", "BLOCK", "INV", "GET_BLOCK_HEADERS","BLOCK_HEADERS", "GET_BLOCK"}
PRIORITY_MEDIUM = {"TX", "HELLO","RELAY"}
PRIORITY_LOW = {"GETBLOCKHEADERS", "GETBLOCKS"}

DROP_PROB = 0.05
LATENCY_MS = (20, 100)
SEND_RATE_LIMIT = 50  # messages per second

drop_stats = {
    "BLOCK": 0,
    "TX": 0,
    "HELLO": 0,
    "PING": 0,
    "PONG": 0,
    "OTHER": 0
}

priority_order = {
    "BLOCK": 1,
    "TX": 2,
    "PING": 2,
    "PONG": 2,
    "HELLO": 3,
    "BLOCK_HEADERS": 1,
    "INV": 1,
    "GET_BLOCK_HEADERS": 2,
    "GET_BLOCK": 3,
    "RELAY": 3,
}

# Queues per peer and priority
queues = defaultdict(lambda: defaultdict(deque))
retries = defaultdict(int)
lock = threading.Lock()
drop_cnt=0
drop_threshold = 20 # 阈值，超过此值则打印警告
wait_time = 0.02  # 等待时间，单位为秒
# === Sending Rate Limiter ===
class RateLimiter:
    def __init__(self, rate=SEND_RATE_LIMIT):
        self.capacity = rate               # Max burst size
        self.tokens = rate                # Start full
        self.refill_rate = rate           # Tokens added per second
        self.last_check = time.time()
        self.lock = Lock()

    def allow(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_check
            self.tokens += elapsed * self.refill_rate
            self.tokens = min(self.tokens, self.capacity)
            self.last_check = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

rate_limiter = RateLimiter()

def enqueue_message(target_id, ip, port, message):
    from peer_manager import blacklist, rtt_tracker

    # TODO: Check if the peer sends message to the receiver too frequently using the function `is_rate_limited`. If yes, drop the message.
  
    # TODO: Check if the receiver exists in the `blacklist`. If yes, drop the message.
  
    # TODO: Classify the priority of the sending messages based on the message type using the function `classify_priority`.
  
    # TODO: Add the message to the queue (`queues`) if the length of the queue is within the limit `QUEUE_LIMIT`, or otherwise, drop the message.
    # pass

    # 检查黑名单
    if target_id in blacklist:
        return
     
    # 速率限制检查
    if is_rate_limited(target_id):
        return

    # 解析消息类型
    try:
        msg_dict = json.loads(message)
        msg_type = msg_dict.get("type", "UNKNOWN")
    except:
        msg_type = "UNKNOWN"

    # 分类优先级
    priority = classify_priority(msg_type)

    # 入队（检查队列限制）
    with lock:
        if sum(len(q) for q in queues[target_id].values()) < QUEUE_LIMIT:
            queues[target_id][priority].append((message, ip, port))
            #print(f'[debug]Enqueued message to {target_id} with priority {priority} - Type: {msg_type}')
        else:
            # 统计丢弃情况
            drop_stats[msg_type if msg_type in drop_stats else "OTHER"] += 1
            drop_cnt+=1



def is_rate_limited(peer_id):
    # TODO:Check how many messages were sent from the peer to a target peer during the `TIME_WINDOW` that ends now.
  
    # TODO: If the sending frequency exceeds the sending rate limit `RATE_LIMIT`, return `TRUE`; otherwise, record the current sending time into `peer_send_timestamps`.
    # pass
    now = time.time()
    window_start = now - TIME_WINDOW

    # 清理过期时间戳
    with lock:
        timestamps = [ts for ts in peer_send_timestamps[peer_id] if ts > window_start]
        peer_send_timestamps[peer_id] = timestamps

        # 检查是否超限
        if len(timestamps) >= RATE_LIMIT:
            return True
        else:
            peer_send_timestamps[peer_id].append(now)
            return False

def classify_priority(message_type):
    # TODO: Classify the priority of a message based on the message type.
    # pass
    return priority_order.get(message_type, 3)  # 默认低优先级为3
    

def send_from_queue(self_id):
    def worker():
        
        # TODO: Read the message in the queue. Each time, read one message with the highest priority of a target peer. After sending the message, read the message of the next target peer. This ensures the fairness of sending messages to different target peers.

        # TODO: Send the message using the function `relay_or_direct_send`, which will decide whether to send the message to target peer directly or through a relaying peer.

        # TODO: Retry a message if it is sent unsuccessfully and drop the message if the retry times exceed the limit `MAX_RETRIES`.

        # pass
        while True:
            with lock:
                # 找到所有有消息的目标节点
                targets = list(queues.keys())
            if not targets:
                time.sleep(0.1)
                continue

            # 轮询每个目标（公平性）
            for target_id in targets:
                with lock:
                    if target_id not in queues:
                        continue

                    # 按优先级选择消息
                    # 提取当前节点的最高优先级消息
                    message_info = None
                    for priority in sorted(queues[target_id].keys()):
                        if queues[target_id][priority]:
                            message_info = queues[target_id][priority].popleft()
                            break

                    if not message_info:
                        continue   

                # 3. 在锁外处理消息发送（避免阻塞其他操作）
                message, ip, port = message_info
                msg_type = json.loads(message).get("type", "UNKNOWN")
                success = relay_or_direct_send(self_id, target_id, message)

                # 4. 处理重试逻辑（再次短暂加锁）

                with lock:
                    if not success:
                        retries[target_id] += 1
                        if retries[target_id] < MAX_RETRIES:
                            # 重新入队（需再次检查队列长度）
                            time.sleep(RETRY_INTERVAL)  # 等待重试间隔
                            if sum(len(q) for q in queues[target_id].values()) < QUEUE_LIMIT:
                                queues[target_id][priority].append(message_info)
                            else:
                                drop_stats[msg_type if msg_type in drop_stats else "OTHER"] += 1
                                drop_cnt+=1
                                print(f"队列已满，丢弃消息: {message[:50]}...")
                                retries[target_id] = 0
                        else:
                            drop_stats[msg_type if msg_type in drop_stats else "OTHER"] += 1
                            drop_cnt+=1
                            print(f"重试次数超过限制({MAX_RETRIES})，丢弃消息: {message[:50]}...")
                            retries[target_id] = 0
                    else:
                        retries[target_id] = 0
            time.sleep(0.02)

    threading.Thread(target=worker, daemon=True).start()

def relay_or_direct_send(self_id, dst_id, message):
    from peer_discovery import known_peers,is_reachable

    # TODO: Check if the target peer is NATed. 

    # TODO: If the target peer is NATed, use the function `get_relay_peer` to find the best relaying peer. 
    # Define the JSON format of a `RELAY` message, which should include `{message type, sender's ID, target peer's ID, `payload`}`. 
    # `payload` is the sending message. 
    # Send the `RELAY` message to the best relaying peer using the function `send_message`.
  
    # TODO: If the target peer is non-NATed, send the message to the target peer using the function `send_message`.


    if not is_reachable(self_id, dst_id):
        sender_id = json.loads(message).get("sender", self_id)
        relay_peer = get_relay_peer(self_id, dst_id,sender_id)
        if relay_peer:                
            relay_msg = {
                "type": "RELAY",
                "sender": self_id,
                "target": dst_id,
                "payload": message,
                "message_id": generate_message_id()
            }
            return send_message(relay_peer[0], relay_peer[1], json.dumps(relay_msg))
        else:
            print(f"No suitable relay peer found for {dst_id}.")
            return False
    else:
        # 直接发送
        return send_message(known_peers[dst_id][0], known_peers[dst_id][1], message)
        
def get_relay_peer(self_id, dst_id,sender_id):
    from peer_manager import  rtt_tracker ,Lock
    from peer_discovery import known_peers, reachable_by 

    # TODO: Find the set of relay candidates reachable from the target peer in `reachable_by` of `peer_discovery.py`.
    
    # TODO: Read the transmission latency between the sender and other peers in `rtt_tracker` in `peer_manager.py`.
  
    # TODO: Select and return the best relaying peer with the smallest transmission latency.
    # pass
    candidates = reachable_by.get(dst_id, [])
    best_peer = None
    min_rtt = float('inf')

    for peer in candidates:
        if peer == sender_id:
            continue
        with Lock:
            # current_rtt = rtt_tracker.get(peer, 2000)  # 默认2秒
            current_rtt = sum(rtt_tracker.get(peer, [2000])) / len(rtt_tracker.get(peer, [2000]))
        if current_rtt < min_rtt:
            min_rtt = current_rtt
            best_peer = peer

    try:
        return (known_peers[best_peer][0], known_peers[best_peer][1]) if best_peer else None
    except KeyError:
        print(f"Target peer {best_peer} not found in known peers.")
        return None
    
    # return best_peer  # (peer_id, ip, port) or None

def apply_network_conditions(send_func):
    def wrapper(ip, port, message):

        # TODO: Use the function `rate_limiter.allow` to check if the peer's sending rate is out of limit. 
        # If yes, drop the message and update the drop states (`drop_stats`).

        # TODO: Generate a random number. If it is smaller than `DROP_PROB`, drop the message to simulate the random message drop in the channel. 
        # Update the drop states (`drop_stats`).

        # TODO: Add a random latency before sending the message to simulate message transmission delay.

        # TODO: Send the message using the function `send_func`.
        # pass

        #速率限制检查
        if not rate_limiter.allow():
            msg_type = json.loads(message).get("type", "OTHER")
            drop_stats[msg_type if msg_type in drop_stats else "OTHER"] += 1
            drop_cnt += 1
            print(f"当前发送速率过快，丢弃消息: {message[:50]}...")
            return False

        # 随机丢包
        if random.random() < DROP_PROB:
            msg_type = json.loads(message).get("type", "OTHER")
            drop_stats[msg_type if msg_type in drop_stats else "OTHER"] += 1
            drop_cnt += 1
            print(f"当前网络环境不佳，丢弃消息: {message[:50]}...")
            return False

        # 添加延迟
        delay = random.randint(*LATENCY_MS) / 1000
        time.sleep(delay)

        # 实际发送
        try:
            send_func(ip, port, message)
            return True
        except:
            return False
    return wrapper


def send_message(ip, port, message):

    # TODO: Send the message to the target peer. 
    # Wrap the function `send_message` with the dynamic network condition in the function `apply_network_condition` of `link_simulator.py`.
    # pass
    try:
        # 创建TCP Socket
        print(f"[debug]Sending message to {port}- Message: {message}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # 设置超时时间（秒）
            s.connect((ip, port))
            
            # 将消息序列化并发送（不用序列化！！！）

            serialized_msg = message
            if not isinstance(message, str):
                print(f"Message bytes: {message} , no need to encode")
            else:
                serialized_msg = message.encode('utf-8')

            s.sendall(serialized_msg)
            
            
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"发送失败至 {ip}:{port} - 错误: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False


send_message = apply_network_conditions(send_message)


def start_dynamic_capacity_adjustment():
    def adjust_loop():
        # TODO: Peridically change the peer's sending capacity in `rate_limiter` within the range [2, 10].
        # pass
        while True:
            new_capacity = random.randint(2, 10)
            rate_limiter.capacity = new_capacity
            rate_limiter.refill_rate = new_capacity
            time.sleep(30)  # 每30秒调整一次

    threading.Thread(target=adjust_loop, daemon=True).start()


def gossip_message(self_id, message, fanout=3):

    from peer_discovery import known_peers, peer_config

    # TODO: Read the configuration `fanout` of the peer in `peer_config` of `peer_discovery.py`.

    # TODO: Randomly select the number of target peer from `known_peers`, which is equal to `fanout`. If the gossip message is a transaction, skip the lightweight peers in the `know_peers`.

    # TODO: Send the message to the selected target peer and put them in the outbox queue.
    # pass
    # 获取配置的fanout
    fanout = peer_config.get(self_id,{}).get("fanout", 2)

    # 筛选候选节点
    candidates = []
    for peer_id in known_peers:
        # 如果是交易，跳过轻节点
        if (json.loads(message).get("type") == "TX" and peer_config.get("light", False)) or peer_id == self_id:
            continue
        candidates.append(peer_id)

    # 随机选择fanout个目标
    selected = random.sample(candidates, min(fanout, len(candidates)))

    # 加入发送队列
    for peer_id in selected:
        enqueue_message(peer_id, known_peers[peer_id][0], known_peers[peer_id][1], message)


def get_outbox_status():
    # 返回每个peer下所有优先级队列中的完整消息内容
    with lock:
        return {
            peer: {
                priority: list(message_queue)  
                for priority, message_queue in peer_queues.items()
            }
            for peer, peer_queues in queues.items()
        }


def get_drop_stats():
    # TODO: Return the drop states (`drop_stats`).
    # pass
    return drop_stats.copy()

def dec_drop_cnt():
    global drop_cnt
    def loop():
        # 每秒减少一次丢弃计数
        while True:
            with lock:
                if drop_cnt > 0:
                    drop_cnt -= 1
            time.sleep(1)
    threading.Thread(target=loop, daemon=True).start()