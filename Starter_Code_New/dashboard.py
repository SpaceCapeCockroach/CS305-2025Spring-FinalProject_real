from flask import Flask, jsonify, render_template
from threading import Thread
from peer_manager import peer_status, rtt_tracker
from transaction import get_recent_transactions
from outbox import rate_limiter
from message_handler import get_redundancy_stats
from peer_discovery import known_peers,peer_flags,peer_config
import json
from block_handler import received_blocks,orphan_blocks
from outbox import get_outbox_status

app = Flask(__name__)
blockchain_data_ref = None
known_peers_ref = None

def start_dashboard(peer_id, port):
    global blockchain_data_ref, known_peers_ref
    blockchain_data_ref = received_blocks
    known_peers_ref = known_peers
    def run():
        app.run(host="0.0.0.0", port=port)
    Thread(target=run, daemon=True).start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('index.html')
# @app.route('/blocks')
# def blocks():
#     # TODO: display the blocks in the local blockchain.
#     #pass
#     # 展示本地区块链中的区块
#     if blockchain_data_ref is None:
#         return jsonify({"error": "No blockchain data"}), 500
#     blocks = [block.to_dict() if hasattr(block, "to_dict") else str(block) for block in blockchain_data_ref]
#     return jsonify(blocks)
# @app.route('/blocks')
# def blocks():
#     # TODO: display the blocks in the local blockchain.
#     #pass
#     # 展示本地区块链中的区块
#     if blockchain_data_ref is None:
#         return jsonify({"error": "No blockchain data"}), 500
#     blocks = [block.to_dict() if hasattr(block, "to_dict") else str(block) for block in blockchain_data_ref]
#     return jsonify(blocks)
@app.route('/blocks')
def blocks():
    if blockchain_data_ref is None:
        return jsonify({"error": "No blockchain data"}), 500

    # 1. 转换区块为字典格式
    def block_to_dict(block):
        if hasattr(block, "to_dict"):
            return block.to_dict()
        elif isinstance(block, dict):
            return block
        else:
            return str(block)  # 回退方案

    blocks = [block_to_dict(block) for block in blockchain_data_ref]

    # 2. 手动实现父-子关系映射
    parent_child_map = {}  
    block_dict = {}
    
    for block in blocks:
        # 确保区块是字典格式
        if not isinstance(block, dict):
            continue
            
        block_id = block.get("block_id")
        prev_id = block.get("prev_id")
        
        # 填充区块字典
        if block_id is not None:
            block_dict[block_id] = block
        
        # 处理父-子关系映射
        if prev_id is not None:
            # 使用setdefault确保键存在
            if prev_id not in parent_child_map:
                parent_child_map[prev_id] = []
            parent_child_map[prev_id].append(block_id)

    # 3. 找出所有根区块 (prev_id为空或不存在)
    root_blocks = [
        block for block in blocks
        if block.get("prev_id") in (None, "", 64*'0')  # 涵盖各种空值情况
    ]

    # 4. 递归构建树状结构
    def build_tree(current_id):
        block = block_dict.get(current_id)
        if not block:
            return None
        
        # 创建当前区块的树节点
        node = {
            "block": block,
            "children": []
        }
        
        # 添加子区块（如果存在）
        for child_id in parent_child_map.get(current_id, []):
            child_node = build_tree(child_id)
            if child_node:
                node["children"].append(child_node)
                
        return node

    # 从每个根节点构建树
    tree_data = []
    for root_block in root_blocks:
        root_id = root_block.get("block_id")
        if root_id:
            tree = build_tree(root_id)
            if tree:
                tree_data.append(tree)

    return jsonify(tree_data)


@app.route('/peers')
def peers():
    peers_info = []
    # 遍历所有已知节点的ID
    for peer_id in known_peers_ref:
        # 基础信息获取
        ip, port = known_peers_ref.get(peer_id, ("unknown", "unknown"))
        flags = peer_flags.get(peer_id, {})
        status = peer_status.get(peer_id, "UNREACHABLE")
        localnetwork_id= peer_config.get(peer_id, {}).get("localnetworkid", "public")
        
        if not localnetwork_id:
            localnetwork_id = "public"
        
        # 构建节点信息字典
        current_rtt = sum(rtt_tracker.get(peer_id, [1000])) / len(rtt_tracker.get(peer_id, [1000])) if peer_status.get(peer_id) == "ALIVE" else 0
        peer_data = {
            "peer_id": peer_id,
            "ip": ip,
            "port": port,
            "status": status,
            "NATed": flags.get("nat", False),
            "type": "lightweight" if flags.get("light", False) else "full",
            "latency": f"{current_rtt:.2f}ms",
            "localnetworkid": localnetwork_id
        }
        
        peers_info.append(peer_data)
    
    return jsonify(sorted(peers_info, key=lambda x: x["peer_id"]))

@app.route('/transactions')
def transactions():
    # TODO: display the transactions in the local pool `tx_pool`.
    #pass
    txs = get_recent_transactions()
    return jsonify(txs)

@app.route('/latency')
def latency():
    # TODO: display the transmission latency between peers.
    #pass
    # 展示节点间的延迟
    latency_info = []
    for peer in rtt_tracker:
        current_rtt = sum(rtt_tracker.get(peer, [1000])) / len(rtt_tracker.get(peer, [1000]))
        latency_info.append({"peer_id": peer, "latency_ms": current_rtt})
    return jsonify(latency_info)

@app.route('/capacity')
def capacity():
    # TODO: display the sending capacity of the peer.
    #pass
    # 展示本节点的发送能力
    capacity = rate_limiter.capacity
    return jsonify({"capacity": capacity})

@app.route('/orphans')
def display_orphan_blocks():
    # TODO: display the orphaned blocks.
    #pass
    orphan_blocks_info = []
    for prev_id, blocks in orphan_blocks.items():
        for block in blocks:
            orphan_blocks_info.append({
                "prev_id": prev_id,
                "block_id": block.get("block_id", "unknown"),
                "timestamp": block.get("timestamp", "unknown"),
                "tx_count": len(block.get("tx_list", []))
            })
    return jsonify(orphan_blocks_info)

@app.route('/redundancy')
def redundancy_stats():
    # TODO: display the number of redundant messages received.
    #pass
    # 展示收到的冗余消息数
    stats = get_redundancy_stats()
    return jsonify(stats)

@app.route('/outbox')
def outbox_status():
    try:
        raw_outbox_data = get_outbox_status() 
        
        formatted_data = {}
        priority_map = {
            "1": "high",
            "2": "medium",
            "3": "low" 
        }

        for peer_id, priorities_map in raw_outbox_data.items():
            formatted_priorities = {}
            for pri_key, messages in priorities_map.items():
                pri_name = priority_map.get(str(pri_key), f"unknown_priority_{pri_key}")
                formatted_priorities[pri_name] = messages 
            formatted_data[peer_id] = formatted_priorities
        
        return jsonify({
            "message": "Outbox queue status with full message details",
            "data": formatted_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500