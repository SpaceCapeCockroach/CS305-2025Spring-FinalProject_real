import json
import threading
import time
import hashlib
import random
from collections import defaultdict
from peer_discovery import handle_hello_message, known_peers, peer_config,peer_flags
from block_handler import handle_block, get_block_by_id, create_getblock, received_blocks, header_store,orphan_blocks
from inv_message import  create_inv, get_inventory
from block_handler import create_getblock
from peer_manager import  update_peer_heartbeat, record_offense, create_pong, handle_pong
from transaction import add_transaction
from outbox import enqueue_message, gossip_message
from utils import generate_message_id
from block_handler import compute_block_hash

# === Global State ===
SEEN_EXPIRY_SECONDS = 600  # 10 minutes
seen_message_ids = {}
seen_txs = set()
redundant_blocks = 0
redundant_txs = 0
message_redundancy = 0
peer_inbound_timestamps = defaultdict(list)
seen_lock = threading.RLock()

# === Inbound Rate Limiting ===
INBOUND_RATE_LIMIT = 20
INBOUND_TIME_WINDOW = 10  # seconds

def is_inbound_limited(peer_id):
    # TODO: Record the timestamp when receiving message from a sender.

    # TODO: Check if the number of messages sent by the sender exceeds `INBOUND_RATE_LIMIT` during the `INBOUND_TIME_WINDOW`. If yes, return `TRUE`. If not, return `FALSE`.

    # pass
    now = time.time()
    window_start = now - INBOUND_TIME_WINDOW

    # 清理过期记录
    timestamps = [ts for ts in peer_inbound_timestamps[peer_id] if ts > window_start]
    peer_inbound_timestamps[peer_id] = timestamps
    
    # 记录当前时间戳
    peer_inbound_timestamps[peer_id].append(now)

    # 检查是否超限
    return len(timestamps) > INBOUND_RATE_LIMIT

# ===  Redundancy Tracking ===
def get_redundancy_stats():
    # TODO: Return the times of receiving duplicated messages (`message_redundancy`).
    # pass
    return {
        "message_redundancy": message_redundancy,
        "redundant_blocks": redundant_blocks,
        "redundant_txs": redundant_txs
    }

# === Main Message Dispatcher ===
def dispatch_message(msg_raw, self_id, self_ip):
    try:
        msg = json.loads(msg_raw)
    except json.JSONDecodeError:
        print(f"[{self_id}] {msg_raw}无效的JSON消息")
        return
    print(f"raw_msg:{msg_raw}\n")

    if not isinstance(msg, dict):
        print(f"[{self_id}] 消息格式不是字典！！！！！")
        return
    msg_type = msg["type"]

    # TODO: Read the message.

    # TODO: Check if the message has been seen in `seen_message_ids` to prevent replay attacks. If yes, drop the message and add one to `message_redundancy`. If not, add the message ID to `seen_message_ids`.

    # TODO: Check if the sender sends message too frequently using the function `in_bound_limited`. If yes, drop the message.

    # TODO: Check if the sender exists in the `blacklist` of `peer_manager.py`. If yes, drop the message.

    sender_id = msg["sender"]

    if sender_id not in known_peers and msg_type != "HELLO":
        print(f"[{self_id}] 未知节点 {sender_id} 发送的非HELLO消息,丢弃")
        return
    
    try:
        msg_id = msg["message_id"]
    except Exception as e:
        print(f"message_id Exception: {e}")
        print("没有id的message")
    msg_type = msg["type"]


    from peer_manager import blacklist
    if sender_id in blacklist:
        print(f"[{self_id}] 拦截黑名单节点 {sender_id} 的消息")
        return
    
    # 检查消息ID重复
    with seen_lock:
        if msg_id in seen_message_ids:
            if time.time() - seen_message_ids[msg_id] < SEEN_EXPIRY_SECONDS:
                global message_redundancy
                message_redundancy += 1
                print(f"[{self_id}] 重复消息 {msg_id[:8]}... 已丢弃")
                return
        seen_message_ids[msg_id] = time.time()

    # 入站速率限制
    if is_inbound_limited(sender_id):
        print(f"[{self_id}] 节点, sender: {sender_id} 触发入站速率限制")
        return
    

    if msg_type == "RELAY":

        # TODO: Check if the peer is the target peer.
        # If yes, extract the payload and recall the function `dispatch_message` to process the payload.
        # If not, forward the message to target peer using the function `enqueue_message` in `outbox.py`.
        # pass
        target_id = msg.get("target")
        if target_id == self_id:
            # 处理实际负载
            payload_raw = msg["payload"]
            
            dispatch_message(payload_raw, self_id, self_ip)
        else:
            # 转发给目标节点
            enqueue_message(target_id, known_peers[target_id][0],known_peers[target_id][1], msg_raw)  # 假设已知节点信息


    elif msg_type == "HELLO":
        # TODO: Call the function `handle_hello_message` in `peer_discovery.py` to process the message.
        # pass
        handle_hello_message(msg_raw, self_id)

    elif msg_type == "BLOCK":
        # TODO: Check the correctness of block ID. If incorrect, record the sender's offence using the function `record_offence` in `peer_manager.py`.
        
        # TODO: Call the function `handle_block` in `block_handler.py` to process the block.
        
        # TODO: Call the function `create_inv` to create an `INV` message for the block.
        
        # TODO: Broadcast the `INV` message to known peers using the function `gossip_message` in `outbox.py`.

        # pass
        
        
        # 验证区块哈希
        computed_hash = compute_block_hash(msg)
        if msg.get("block_id") != computed_hash:
            print(f"[{self_id}] 无效区块哈希 from {sender_id}")
            record_offense(sender_id)
            return
            
        handle_block(msg_raw, self_id)


    elif msg_type == "TX":
        
        # TODO: Check the correctness of transaction ID. If incorrect, record the sender's offence using the function `record_offence` in `peer_manager.py`.
        
        # TODO: Add the transaction to `tx_pool` using the function `add_transaction` in `transaction.py`.
        
        # TODO: Broadcast the transaction to known peers using the function `gossip_message` in `outbox.py`.

        # pass
        from transaction import TransactionMessage
        tx = TransactionMessage.from_dict(msg)
        tx_id = msg.get("id")
        if tx_id != tx.compute_hash():
            print(f"[{self_id}] 无效交易 from {sender_id}")
            record_offense(sender_id)
            return
            
        if peer_flags[self_id].get("light", False):
            print(f"[{self_id}] 轻节点收到交易 {tx_id[:8]}，转发给其他节点")
            gossip_message(self_id, msg_raw)
            return
        
        # 检查交易是否已存在
        if add_transaction(tx):
            gossip_message(self_id, msg_raw)

    elif msg_type == "PING":
        
        # TODO: Update the last ping time using the function `update_peer_heartbeat` in `peer_manager.py`.
        
        # TODO: Create a `pong` message using the function `create_pong` in `peer_manager.py`.
        
        # TODO: Send the `pong` message to the sender using the function `enqueue_message` in `outbox.py`.

        # pass
        update_peer_heartbeat(sender_id)
        pong_msg = create_pong(self_id, msg["timestamp"])
        print(f"[{self_id}] 收到PING消息 from {sender_id}，回复PONG")
        enqueue_message(sender_id, known_peers[sender_id][0],known_peers[sender_id][1], json.dumps(pong_msg))  # 假设已知节点信息

    elif msg_type == "PONG":
        
        # TODO: Update the last ping time using the function `update_peer_heartbeat` in `peer_manager.py`.
        
        # TODO: Call the function `handle_pong` in `peer_manager.py` to handle the message.

        # pass
        update_peer_heartbeat(sender_id)
        handle_pong(msg_raw)

    elif msg_type == "INV":
        
        # TODO: Read all blocks IDs in the local blockchain using the function `get_inventory` in `block_handler.py`.
        
        # TODO: Compare the local block IDs with those in the message.
        
        # TODO: If there are missing blocks, create a `GETBLOCK` message to request the missing blocks from the sender.
        
        # TODO: Send the `GETBLOCK` message to the sender using the function `enqueue_message` in `outbox.py`.

        # pass
        print(f"[{self_id}] 收到INV消息 from {sender_id}，包含区块ID: {msg['block_ids']}")
        if peer_flags[self_id].get("light", False):
            print(f"[{self_id}] 轻节点收到INV消息，忽略区块请求")
            return
        
        # 全节点处理
        local_inv = get_inventory()
        remote_inv = set(msg["block_ids"])
        missing = remote_inv - set(local_inv)
        
        if missing:
            print(f"[{self_id}] 缺少区块 from {sender_id}，区块ID: {msg['block_ids']}，发起请求...")
            getblock_msg = create_getblock(self_id, list(missing))
            enqueue_message(sender_id, known_peers[sender_id][0],known_peers[sender_id][1], json.dumps(getblock_msg))
        else:
            print(f"[{self_id}] 已拥有所有区块 from {sender_id}，无需请求")

    elif msg_type == "GET_BLOCK":
        
        # TODO: Extract the block IDs from the message.
        
        # TODO: Get the blocks from the local blockchain according to the block IDs using the function `get_block_by_id` in `block_handler.py`.
        
        # TODO: If the blocks are not in the local blockchain, create a `GETBLOCK` message to request the missing blocks from known peers.
        
        # TODO: Send the `GETBLOCK` message to known peers using the function `enqueue_message` in `outbox.py`.
        
        # TODO: Retry getting the blocks from the local blockchain. If the retry times exceed 3, drop the message.
        
        # TODO: If the blocks exist in the local blockchain, send the blocks one by one to the requester using the function `enqueue_message` in `outbox.py`.

        # pass
       
        requested = msg["request_ids"]
        # retries = msg.get("retries", 0)
        
        found = []
        if peer_flags[self_id].get("light", False):          
            for peer_id, (ip, port) in known_peers.items():
                if peer_id == self_id or peer_id == sender_id: continue
                print(f"[{self_id}] 轻节点收到区块请求 ，忽略")
                #enqueue_message(peer_id, ip, port, msg_raw)
            return
        
        missing_blocks = list(requested)
            # 尝试从本地区块链获取区块
        for i in range(4):  # 最多重新尝试3次 
            cur_miss_bids=[]
            request_delay=5**i
            for bid in missing_blocks:
                block = get_block_by_id(bid)
                if block:
                    found.append(block)
                    break
                else:
                    cur_miss_bids.append(bid)
                # if is_orphan(bid):
                #     request_par
                    if i ==3:
                        print(f"[{self_id}] 无法获取区块 {bid[:8]}，已放弃...")
                        break
            # 如果区块不在本地，尝试从其他节点获取
            missing_blocks = cur_miss_bids
            if not missing_blocks:
                print(f"[{self_id}] 所有请求区块 {len(found)} 个都找到了")
                break
            else:
                new_getblock = create_getblock(self_id, missing_blocks)
                for peer_id, (ip, port) in known_peers.items():
                    if peer_id == self_id or peer_id == sender_id: continue
                    time.sleep(0.02)
                    enqueue_message(peer_id, ip, port, json.dumps(new_getblock))
                    print(f"[{self_id}] 未找到区块 {len(missing_blocks)} 个，已请求其他节点")
                    time.sleep(request_delay)
                # 如果是全节点，创建GETBLOCK请求
                #     new_getblock = create_getblock(self_id, [bid])
                #     for peer_id, (ip, port) in known_peers.items():
                #         if peer_id == self_id or peer_id == sender_id: continue
                #         time.sleep(0.02)  # 添加间隔，避免同时发送
                #         enqueue_message(peer_id, ip, port, json.dumps(new_getblock))
                #     # gossip_message(self_id, json.dumps(new_getblock))
                # time.sleep(request_delay)  # 等待一段时间再重试
        
        # 发送找到的区块
        for block in found:
            enqueue_message(sender_id, known_peers[sender_id][0],known_peers[sender_id][1], json.dumps(block))

    elif msg_type == "GET_BLOCK_HEADERS":
        
        # TODO: Read all block header in the local blockchain and store them in `headers`.
        
        # TODO: Create a `BLOCK_HEADERS` message, which should include `{message type, sender's ID, headers}`.
        
        # TODO: Send the `BLOCK_HEADERS` message to the requester using the function `enqueue_message` in `outbox.py`.

        # pass
        from block_handler import block_lock
        with block_lock:
            headers = [h.copy() for h in header_store]
        response = {
            "type": "BLOCK_HEADERS",
            "sender": self_id,
            "headers": headers,
            "message_id": generate_message_id()
        }
        enqueue_message(sender_id, known_peers[sender_id][0],known_peers[sender_id][1], json.dumps(response))

    elif msg_type == "BLOCK_HEADERS":
        
        # TODO: Check if the previous block of each block exists in the local blockchain or the received block headers.
        
        # TODO: If yes and the peer is lightweight, add the block headers to the local blockchain.
        
        # TODO: If yes and the peer is full, check if there are missing blocks in the local blockchain. If there are missing blocks, create a `GET_BLOCK` message and send it to the sender.
        
        # TODO: If not, drop the message since there are orphaned blocks in the received message and, thus, the message is invalid.

        # pass
        from block_handler import block_lock
        with block_lock:
            current_chain = {h["hash"]: h for h in header_store}
            current_blocks = {b["block_id"]: b for b in received_blocks}
            or_blocks = {
                block["block_id"]: block  # 键和值表达式
                for blocks_list in orphan_blocks.values()  # 外层循环（每个值都是block列表）
                for block in blocks_list  # 内层循环（遍历列表中的每个block）
            }

        for hdr in msg["headers"]:
            prev_hash = hdr["prev_hash"]
            if prev_hash not in current_chain and prev_hash != "0"*64:
                print(f"[{self_id}] 收到孤块头 {hdr['hash'][:8]}...")
                return
                
        # 全节点和轻节点处理
        with block_lock:
            # 去重检查
            new_headers = [
                hdr for hdr in msg["headers"]
                if hdr["hash"] not in current_chain
            ]
            header_store.extend(new_headers)
            current_chain = {h["hash"]: h for h in header_store}
            print(f"[{self_id}] 节点添加 {len(new_headers)} 个新区块头")

        # 全节点处理
        is_light_node = peer_config.get(self_id, {}).get("light", False)
        if not is_light_node:
            missing_block_ids = []
            with block_lock:
                for hdr in msg["headers"]:
                    # 块头已存在但完整块缺失
                    if hdr["hash"] in current_chain and (hdr["hash"] not in current_blocks or hdr["hash"] not in or_blocks):
                        missing_block_ids.append(hdr["hash"])

            if missing_block_ids:
                print(f"[{self_id}] 全节点缺失 {len(missing_block_ids)} 个完整块，发起请求")
                getblock_msg = create_getblock(self_id, missing_block_ids)
                enqueue_message(sender_id, known_peers[sender_id][0],known_peers[sender_id][1], json.dumps(getblock_msg))
            else:
                print(f"[{self_id}] 全节点已拥有全部区块，无需处理")


    else:
        print(f"[{self_id}] Unknown message type: {msg_type}", flush=True)