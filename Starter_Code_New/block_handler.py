
import time
import hashlib
import json
import threading
from transaction import get_recent_transactions, clear_pool
from peer_discovery import known_peers, peer_config

from outbox import  enqueue_message, gossip_message
from utils import generate_message_id
from peer_manager import record_offense

received_blocks = [] # The local blockchain. The blocks are added linearly at the end of the set.
header_store = [] # The header of blocks in the local blockchain. Used by lightweight peers.
orphan_blocks = {} # The block whose previous block is not in the local blockchain. Waiting for the previous block.

block_lock = threading.RLock()  # Lock for thread-safe access to received_blocks and orphan_blocks

def request_block_sync(self_id):
    # TODO: Define the JSON format of a `GET_BLOCK_HEADERS`, which should include `{message type, sender's ID}`.

    # TODO: Send a `GET_BLOCK_HEADERS` message to each known peer and put the messages in the outbox queue.
    # pass
    get_block_headers_msg = {
        "type": "GET_BLOCK_HEADERS",
        "sender": self_id,
        "message_id": generate_message_id()
    }

    # enqueue_message(target_id, ip, port, message)


    k_peers = known_peers.copy()  # Avoid modifying the dictionary while iterating
    for peer_id, (ip, port) in k_peers.items():
        if peer_id != self_id:

            enqueue_message(
                peer_id,ip, port,
                json.dumps(get_block_headers_msg),
            )

def block_generation(self_id, MALICIOUS_MODE, interval=20):
    from inv_message import create_inv
    def mine():

    # TODO: Create a new block periodically using the function `create_dummy_block`.

    # TODO: Create an `INV` message for the new block using the function `create_inv` in `inv_message.py`.

    # TODO: Broadcast the `INV` message to known peers using the function `gossip` in `outbox.py`.
        # pass
        # DIFFICULTY = 4  # 工作量证明难度（前导零数）
        
        while True:
            # 生成候选区块
            block = create_dummy_block(self_id, MALICIOUS_MODE)
            if not block:
                print("未生成候选区块，等待交易...")
                time.sleep(interval)
                continue

            # 广播新区块
            if 'block_id' in block:
                inv_msg = create_inv(self_id, [block['block_id']])
                gossip_message(self_id,json.dumps(inv_msg))
                print(f"生成新区块 #{len(received_blocks)+1} | Hash: {block['block_id'][:16]}...")
                
            time.sleep(interval)
    threading.Thread(target=mine, daemon=True).start()

def create_dummy_block(peer_id, MALICIOUS_MODE):

    # TODO: Define the JSON format of a `block`, which should include `{message type, peer's ID, timestamp, block ID, previous block's ID, and transactions}`. 
    # The `block ID` is the hash value of block structure except for the item `block ID`. 
    # `previous block` is the last block in the blockchain, to which the new block will be linked. 
    # If the block generator is malicious, it can generate random block ID.

    # TODO: Read the transactions in the local `tx_pool` using the function `get_recent_transactions` in `transaction.py`.

    # TODO: Create a new block with the transactions and generate the block ID using the function `compute_block_hash`.
     
    # TODO: Clear the local transaction pool and add the new block into the local blockchain (`receive_block`).
    # pass
    with block_lock:
        prev_hash = received_blocks[-1]['block_id'] if received_blocks else '0'*64
        transactions = get_recent_transactions()
        
    block = {
        "type": "BLOCK",
        "sender": peer_id,
        "timestamp": time.time(),
        "block_id": "",  # Will be computed later
        "prev_id": prev_hash,
        "tx_list": transactions,
        "message_id": generate_message_id()
    }
    
    # 恶意节点篡改前哈希
    if MALICIOUS_MODE:
        block['block_id'] = hashlib.sha256(str(time.time()).encode()).hexdigest()
    else:
        block['block_id'] = compute_block_hash(block)

    return block

def compute_block_hash(block):
    # TODO: Compute the hash of a block except for the term `block ID`.
    # pass
    block_copy = block.copy()
    if 'block_id' in block_copy:
        del block_copy['block_id']
        
    return hashlib.sha256(
        json.dumps(block_copy, sort_keys=True).encode()
    ).hexdigest()


def handle_block(msg, self_id):
    # TODO: Check the correctness of `block ID` in the received block. If incorrect, drop the block and record the sender's offence.

    # TODO: Check if the block exists in the local blockchain. If yes, drop the block.

    # TODO: Check if the previous block of the block exists in the local blockchain. If not, add the block to the list of orphaned blocks (`orphan_blocks`). If yes, add the block to the local blockchain.

    # TODO: Check if the block is the previous block of blocks in `orphan_blocks`. If yes, add the orphaned blocks to the local blockchain.
    # pass
    try:
        # if(self_id == 'system'):
        #     # 系统消息，直接处理
            
        #     pass

        block = json.loads(msg)
        sender_id = block.get('creator')
            
        # 计算实际哈希
        computed_hash = compute_block_hash(block)
        if block['block_id'] != computed_hash:
            print(f"无效区块哈希: 声明 {block['block_id'][:8]} 实际 {computed_hash[:8]}")
            record_offense(sender_id)
            return
            
        with block_lock:
            # 重复检查
            if any(b['block_id'] == block['block_id'] for b in received_blocks):
                return
                
            # 主链连接检查
            if block['prev_hash'] == (received_blocks[-1]['block_id'] if received_blocks else '0'*64):
                add_to_chain(block,self_id)
                check_orphans(block['block_id'])
            else:
                # 存入孤儿区块
                orphan_blocks.setdefault(block['prev_hash'], []).append(block)
                print(f"孤儿区块 | 前哈希: {block['prev_hash'][:8]}...")
                
    except (KeyError, json.JSONDecodeError) as e:
        print(f"区块解析失败: {e}")


def add_to_chain(block,self_id):
    """添加区块到主链"""
    with block_lock:
        if not peer_config.get(self_id, {}).get('light', False):
            # 如果不是轻节点，添加到主链
            received_blocks.append(block)
            
        header_store.append({
            'hash': block['block_id'],
            'timestamp': block['timestamp'],
            'tx_count': len(block['tx_list']),
            'prev_hash': block['prev_id']
        })
        clear_pool()
        print(f"新区块确认 | 高度: {len(received_blocks)}")

def check_orphans(new_hash):
    """检查孤儿区块"""
    if new_hash in orphan_blocks:
        print(f"处理孤儿区块 | 前哈希: {new_hash[:8]}...")

        for orphan in orphan_blocks[new_hash]:
            handle_block(json.dumps(orphan), 'system')
        del orphan_blocks[new_hash]


def create_getblock(sender_id, requested_ids):
    # TODO: Define the JSON format of a `GETBLOCK` message, which should include `{message type, sender's ID, requesting block IDs}`.
    # pass
    """构造区块请求消息"""
    return {
        "type": "GETBLOCK",
        "sender": sender_id,
        "request_ids": requested_ids,
        "message_id": generate_message_id()
    }


def get_block_by_id(block_id):
    # TODO: Return the block in the local blockchain based on the block ID.
    # pass
    with block_lock:
        for block in received_blocks:
            if block['block_id'] == block_id:
                return block
        for orphans in orphan_blocks.values():
            for block in orphans:
                if block['block_id'] == block_id:
                    return block
                
    # 如果没有找到，返回None
    print(f"区块 {block_id[:8]} 未找到")
    return None



