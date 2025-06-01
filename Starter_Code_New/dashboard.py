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
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')
@app.route('/blocks')
def blocks():
    # TODO: display the blocks in the local blockchain.
    #pass
    # 展示本地区块链中的区块
    if blockchain_data_ref is None:
        return jsonify({"error": "No blockchain data"}), 500
    blocks = [block.to_dict() if hasattr(block, "to_dict") else str(block) for block in blockchain_data_ref]
    return jsonify(blocks)


@app.route('/peers')
def peers():
    peers_info = []
    # 遍历所有已知节点的ID
    for peer_id in known_peers_ref:
        # 基础信息获取
        ip, port = known_peers_ref.get(peer_id, ("unknown", "unknown"))
        flags = peer_flags.get(peer_id, {})
        status = peer_status.get(peer_id, "UNREACHABLE")
        localnetwork_id= peer_config.get(peer_id, {}).get("localnetworkid", "unknown")
        
        if not localnetwork_id:
            localnetwork_id = "unknown"
        
        # 构建节点信息字典
        peer_data = {
            "peer_id": peer_id,
            "ip": ip,
            "port": port,
            "status": status,
            "NATed": flags.get("nat", False),
            "type": "lightweight" if flags.get("light", False) else "full",
            "latency": f"{rtt_tracker.get(peer_id, 0):.2f}ms",
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
    for peer_id, rtt in rtt_tracker.items():
        latency_info.append({"peer_id": peer_id, "latency_ms": rtt})
    return jsonify(latency_info)

@app.route('/capacity')
def capacity():
    # TODO: display the sending capacity of the peer.
    #pass
    # 展示本节点的发送能力
    capacity = rate_limiter.capacity
    return jsonify({"capacity": capacity})

@app.route('/orphans')
def orphan_blocks():
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
    """ 展示待发送消息队列状态 """
    try:
        # 获取原始队列状态
        raw_status = get_outbox_status()
        
        # 转换为更易读的格式
        formatted_status = {}
        for peer_id, priorities in raw_status.items():
            formatted_status[peer_id] = {
                "high_priority": priorities.get(1, 0),
                "medium_priority": priorities.get(2, 0),
                "low_priority": priorities.get(3, 0),
                "total": sum(priorities.values())
            }
        
        return jsonify({
            "message": "Outbox queue status",
            "data": formatted_status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

