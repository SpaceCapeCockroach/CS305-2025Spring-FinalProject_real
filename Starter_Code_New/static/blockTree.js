// blockTree.js
import { updateBlocksUI, formatTimeAgo } from './ui.js'; // Import necessary UI functions

/**
 * Renders the block tree structure recursively into a given container.
 * @param {Array<object>|object} data - The block tree data. Can be an array of root nodes or a single root node object.
 * @param {HTMLElement} container - The DOM element to render the tree into.
 */
export function renderBlockTree(data, container) {
    if (!data || (Array.isArray(data) && data.length === 0)) {
        container.innerHTML = '<div class="empty-message">区块链为空或无数据返回</div>';
        return;
    }
    container.innerHTML = ''; // Clear previous content

    /**
     * Recursively renders a single block node and its children.
     * @param {object} node - The current block node object.
     * @param {HTMLElement} parentElement - The DOM element to append the current node to.
     * @param {number} level - The current depth level in the tree (for initial expansion).
     */
    function renderNode(node, parentElement, level) {
        if (!node || !node.block) {
            console.warn("Invalid block node encountered, skipping:", node);
            return;
        }

        const blockNode = document.createElement('div');
        blockNode.className = 'block-node';
        
        const blockHeader = document.createElement('div');
        blockHeader.className = 'block-header';
        blockNode.appendChild(blockHeader);
        
        const toggleIcon = document.createElement('div');
        toggleIcon.className = 'toggle-icon';
        blockHeader.appendChild(toggleIcon);
        
        const indicator = document.createElement('div');
        indicator.className = 'block-indicator';
        blockHeader.appendChild(indicator);
        
        const blockInfo = document.createElement('div');
        blockInfo.className = 'block-info';
        blockHeader.appendChild(blockInfo);
        
        const blockId = document.createElement('div');
        blockId.className = 'block-id';
        blockId.textContent = `区块 ID: ${node.block.block_id.substring(0,12)}...`;
        blockId.title = node.block.block_id; // Full ID on hover
        blockInfo.appendChild(blockId);
        
        const blockHash = document.createElement('div'); 
        blockHash.className = 'block-hash'; 
        const prevIdDisplay = (node.block.prev_id === "0000000000000000000000000000000000000000000000000000000000000000" || node.block.prev_id === "000000") 
                                    ? '创世块' 
                                    : (node.block.prev_id ? node.block.prev_id.substring(0,12) + '...' : 'N/A');
        blockHash.textContent = `父区块: ${prevIdDisplay}`;
        blockHash.title = node.block.prev_id; // Full parent ID on hover
        blockInfo.appendChild(blockHash);
        
        const detailsContainer = document.createElement('div');
        detailsContainer.className = 'block-details';
        blockNode.appendChild(detailsContainer);
        
        const senderInfo = document.createElement('div');
        senderInfo.className = 'detail-row';
        senderInfo.innerHTML = `<span class="detail-label">生产者:</span><span class="detail-value">${node.block.sender || '未知'}</span>`;
        detailsContainer.appendChild(senderInfo);
        
        const timestampInfo = document.createElement('div');
        timestampInfo.className = 'detail-row';
        const time = new Date(node.block.timestamp * 1000); // Convert Unix timestamp to milliseconds
        timestampInfo.innerHTML = `<span class="detail-label">时间:</span><span class="detail-value">${time.toLocaleString()}</span>`;
        detailsContainer.appendChild(timestampInfo);

        if (node.block.message_id) {
            const msgIdInfo = document.createElement('div');
            msgIdInfo.className = 'detail-row';
            msgIdInfo.innerHTML = `<span class="detail-label">消息ID:</span><span class="detail-value">${node.block.message_id}</span>`;
            detailsContainer.appendChild(msgIdInfo);
        }
        
        if (node.block.tx_list && node.block.tx_list.length) {
            const txInfo = document.createElement('div');
            txInfo.className = 'detail-row';
            txInfo.innerHTML = `<span class="detail-label">交易数:</span><span class="detail-value">${node.block.tx_list.length}</span>`;
            detailsContainer.appendChild(txInfo);
            
            const txList = document.createElement('div');
            txList.className = 'tx-list';
            node.block.tx_list.slice(0, 3).forEach(tx => { // Show first 3 transactions
                const txItem = document.createElement('div');
                txItem.className = 'tx-item';
                const txDisplayId = (tx.tx_id || tx.message_id || '未知交易');
                txItem.textContent = `TX: ${txDisplayId.substring(0,20)}...`;
                txItem.title = txDisplayId; // Full transaction ID on hover
                txList.appendChild(txItem);
            });
            if (node.block.tx_list.length > 3) {
                const more = document.createElement('div');
                more.className = 'tx-item';
                more.style.fontStyle = 'italic';
                more.textContent = `+ ${node.block.tx_list.length - 3} 更多交易...`;
                txList.appendChild(more);
            }
            detailsContainer.appendChild(txList);
        }
        
        let childrenContainer;
        const initiallyExpanded = level < 1; // Expand nodes at level 0 (root nodes) by default

        if (node.children && node.children.length > 0) {
            childrenContainer = document.createElement('div');
            childrenContainer.className = 'children-container';
            blockNode.appendChild(childrenContainer);
            
            // Set initial display state
            detailsContainer.style.display = initiallyExpanded ? 'block' : 'none';
            childrenContainer.style.display = initiallyExpanded ? 'block' : 'none';
            toggleIcon.innerHTML = `<i class="fas ${initiallyExpanded ? 'fa-minus' : 'fa-plus'}"></i>`;

            // Recursively render children
            node.children.forEach(child => {
                renderNode(child, childrenContainer, level + 1);
            });
        } else {
            toggleIcon.innerHTML = '•'; // Use a bullet for leaf nodes (no children)
            detailsContainer.style.display = initiallyExpanded ? 'block' : 'none';
        }
        
        // Add click event listener to toggle details and children
        blockHeader.addEventListener('click', function() {
            const detailsAreVisible = detailsContainer.style.display === 'block';
            const newDisplayState = detailsAreVisible ? 'none' : 'block';
            
            detailsContainer.style.display = newDisplayState;
            if (childrenContainer) { // Only toggle children if they exist
                childrenContainer.style.display = newDisplayState;
                toggleIcon.innerHTML = `<i class="fas ${newDisplayState === 'block' ? 'fa-minus' : 'fa-plus'}"></i>`;
            }
        });
        parentElement.appendChild(blockNode);
    }

    // Start rendering from the root node(s)
    if (Array.isArray(data)) {
        data.forEach(rootNode => renderNode(rootNode, container, 0));
    } else if (typeof data === 'object' && data !== null && data.block) {
        // Handle case where a single root node object is returned (less common for a list endpoint but possible)
         renderNode(data, container, 0);
    } else {
        console.error("Block data is not in expected array or object format:", data);
        container.innerHTML = '<div class="empty-message">区块数据格式错误</div>';
    }
}

/**
 * Helper function to extract all blocks from the tree structure and sort them by timestamp.
 * This is primarily used for the "Latest Blocks" section on the overview page, which needs a flat list.
 * @param {Array<object>} treeData - The block tree data (array of root nodes).
 * @returns {Array<object>} - A flat, sorted (descending by timestamp) array of block objects.
 */
export function extractAndSortBlocksFromTree(treeData) {
    const flatBlocks = [];
    const uniqueBlockIds = new Set(); // To prevent duplicate blocks if they appear in multiple branches

    function traverse(nodes) {
        if (!Array.isArray(nodes)) return;
        nodes.forEach(node => {
            if (node && node.block) {
                if (!uniqueBlockIds.has(node.block.block_id)) {
                     flatBlocks.push({
                        hash: node.block.block_id, // Use 'hash' for consistency with updateBlocksUI
                        transactions: node.block.tx_list || [],
                        timestamp: node.block.timestamp
                    });
                    uniqueBlockIds.add(node.block.block_id);
                }
                if (node.children && node.children.length > 0) {
                    traverse(node.children); // Recurse into children
                }
            }
        });
    }
    traverse(treeData);
    // Sort blocks by timestamp in descending order (latest first)
    return flatBlocks.sort((a, b) => b.timestamp - a.timestamp);
}