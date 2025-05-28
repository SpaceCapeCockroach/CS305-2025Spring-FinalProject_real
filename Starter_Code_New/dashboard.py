from flask import Flask, jsonify
from threading import Thread
from peer_manager import peer_status, rtt_tracker
from transaction import get_recent_transactions
from outbox import rate_limiter
from message_handler import get_redundancy_stats
from peer_discovery import known_peers
import json
from block_handler import received_blocks

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
    return "Block P2P Network Simulation"

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
    # TODO: display the information of known peers, including `{peer's ID, IP address, port, status, NATed or non-NATed, lightweight or full}`.
    #pass
    # 展示已知节点信息
    if known_peers_ref is None:
        return jsonify({"error": "No peer data"}), 500
    peers_info = []
    for peer_id, peer_info in known_peers_ref.items():
        info = {
            "peer_id": peer_id,
            "ip": info.get("ip"),
            "port": info.get("port"),
            "status": peer_status.get(peer_id, "unknown"),
            # "NATed": peer.get("NATed", False),
            # "type": "full" if peer.get("is_full", False) else "lightweight"
        }
        peers_info.append(info)
    return jsonify(peers_info)

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
    pass

@app.route('/redundancy')
def redundancy_stats():
    # TODO: display the number of redundant messages received.
    #pass
    # 展示收到的冗余消息数
    stats = get_redundancy_stats()
    return jsonify(stats)


