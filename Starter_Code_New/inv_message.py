import time
import json
from utils import generate_message_id
from outbox import gossip_message


def create_inv(sender_id, block_ids):
    # TODO: * Define the JSON format of an `INV` message, which should include `{message type, sender's ID, sending blocks' IDs, message ID}`.
    # Note that `INV` messages are sent before sending blocks. 
    # `sending blocks' IDs` is the ID of blocks that the sender want to send. 
    # `message ID` can be a random number generated by `generate_message_id` in `util.py`.
    # pass
    return {
        "type": "INV",
        "sender": sender_id,
        "block_ids": block_ids,
        "message_id": generate_message_id()
    }


def get_inventory():
    # TODO: Return the block ID of all blocks in the local blockchain.
    # pass
    from block_handler import received_blocks, block_lock
    with block_lock:
        print(f"获取本地区块链的区块数量: {len(received_blocks)}")
        return [block["block_id"] for block in received_blocks]
        #return a list of block IDs from the received_blocks list

def broadcast_inventory(self_id):
    # TODO: Create an `INV` message with all block IDs in the local blockchain.

    # TODO: Broadcast the `INV` message to known peers using the function `gossip_message` in `outbox.py` to synchronize the blockchain with known peers.

    # pass
    local_block_ids = get_inventory()
    inv_msg = create_inv(self_id, local_block_ids)
    
    # 向所有已知节点发送
    gossip_message(self_id,json.dumps(inv_msg))


