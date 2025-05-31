import time
import json
import hashlib
import random
import threading
from peer_discovery import known_peers
from outbox import gossip_message
from utils import generate_message_id

class TransactionMessage:
    def __init__(self, sender, receiver, amount, timestamp=None):
        self.type = "TX"
        self.from_peer = sender
        self.to_peer = receiver
        self.amount = amount
        self.timestamp = timestamp if timestamp else time.time()
        self.id = self.compute_hash()
        self.message_id = generate_message_id()

    def compute_hash(self):
        tx_data = {
            "type": self.type,
            "sender": self.from_peer,
            "to": self.to_peer,
            "amount": self.amount,
            "timestamp": self.timestamp
        }
        return hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return {
            "type": self.type,
            "id": self.id,
            "sender": self.from_peer,
            "to": self.to_peer,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }

    @staticmethod
    def from_dict(data):
        return TransactionMessage(
            sender=data["sender"],
            receiver=data["to"],
            amount=data["amount"],
            timestamp=data["timestamp"]
        )
    
tx_pool = [] # local transaction pool
tx_ids = set() # the set of IDs of transactions in the local pool
tx_lock = threading.Lock()  # Lock for thread-safe access to tx_pool and tx_ids
def transaction_generation(self_id, interval=15):
    def loop():
        # TODO: Randomly choose a peer from `known_peers` and generate a transaction to transfer arbitrary amount of money to the peer.

        # TODO:  Add the transaction to local `tx_pool` using the function `add_transaction`.

        # TODO:  Broadcast the transaction to `known_peers` using the function `gossip_message` in `outbox.py`.

        # pass
        BASE_JITTER = 2  # 随机扰动幅度
        
        while True:
            # # 添加随机扰动防止同步
            # sleep_time = interval + random.uniform(-BASE_JITTER, BASE_JITTER)
            # time.sleep(max(sleep_time, 1))  # 确保最小1秒间隔
            time.sleep(interval)

            # 获取有效候选节点
            candidates = []

            k_peers = known_peers.copy()  # 避免在迭代时修改字典
            candidates = [
                pid for pid in k_peers 
                if pid != self_id and pid not in tx_ids
            ]
            
            if not candidates:
                continue
            
            # 随机生成交易
            receiver = random.choice(candidates)
            amount = random.randint(1, 100)
            tx = TransactionMessage(self_id, receiver, amount)
            
            # 原子化添加交易
            if add_transaction(tx):
                print(f"生成交易 → {receiver}: {amount} coins")
                gossip_message(self_id, json.dumps(tx.to_dict()))
    threading.Thread(target=loop, daemon=True).start()

def add_transaction(tx):
    # TODO: Add a transaction to the local `tx_pool` if it is in the pool.

    # TODO: Add the transaction ID to `tx_ids`.
    """添加交易到池（线程安全）"""
    with tx_lock:
        if tx.id in tx_ids:
            return False
        
        # 验证交易有效性
        # if not _validate_transaction(tx):
        #     return False
        print(f"在add_transaction中添加交易到交易池: {tx.to_peer} -> {tx.from_peer}, 金额: {tx.amount}, ID: {tx.id}")
        tx_pool.append(tx)
        tx_ids.add(tx.id)
        return True
    # pass

def get_recent_transactions():
    # TODO: Return all transactions in the local `tx_pool`.
    # pass
    with tx_lock:
        print(f"获取交易池，当前交易数: {len(tx_pool)}")
        return [tx.to_dict() for tx in tx_pool]

def clear_pool(): 
    global tx_pool, tx_ids
    # Remove all transactions in `tx_pool` and transaction IDs in `tx_ids`.
    print("正打算清空交易池")
    with tx_lock:
        print(f"清空交易池，当前交易数: {len(tx_pool)}")
        tx_pool.clear()
        tx_ids.clear()
    pass