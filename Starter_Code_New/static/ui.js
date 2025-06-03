// ui.js

// 导入必要的API函数
import { fetchOutboxData, fetchOrphanBlocksData } from './api.js'; // <-- 确保导入 fetchOrphanBlocksData
import { renderBlockTree } from './blockTree.js'; // 导入 renderBlockTree，用于孤儿块的样式复用

/**
 * Initializes UI elements with initial values.
 * @param {object} elements - Object containing references to DOM elements.
 * @param {string} peerId - The local node's peer ID.
 * @param {number} startTime - The timestamp when the node started.
 */
export function initUI(elements, peerId, startTime) {
    elements.nodeId.textContent = peerId.substr(0, 6) + '...' + peerId.substr(-4);
    updateUptime(startTime, elements.uptime);
}

/**
 * Updates the uptime display.
 * @param {number} startTime - The timestamp when the node started.
 * @param {HTMLElement} uptimeElement - The DOM element to update.
 */
export function updateUptime(startTime, uptimeElement) {
    const uptimeMs = Date.now() - startTime;
    const days = Math.floor(uptimeMs / (1000 * 60 * 60 * 24));
    const hours = Math.floor((uptimeMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60));
    uptimeElement.textContent = `${days}天 ${hours}小时 ${minutes}分钟`;
}

/**
 * Sets up page navigation logic.
 * @param {object} elements - Object containing references to DOM elements.
 * @param {function} fetchAndRenderBlocksTree - Callback function to load/render blocks tree when its page is active.
 * @param {function} initializeOutboxDetailedView - Callback function to initialize the dedicated outbox detailed view.
 * @param {function} initializeOrphanBlocksPage - Callback function to initialize the orphan blocks page. // <-- 新增参数
 */
export function setupPageNavigationUI(elements, fetchAndRenderBlocksTree, initializeOutboxDetailedView, initializeOrphanBlocksPage) { // <-- 更新函数签名
    const pageElements = {
        overview: elements.overviewPage,
        blocks: elements.blocksPage,
        peers: elements.peersPage,
        transactions: elements.transactionsPage,
        performance: elements.performancePage,
        outbox: elements.outboxPage, // 消息队列页面容器 (现在是详细视图)
        orphan_blocks: elements.orphanBlocksPage, // <-- 新增
        settings: elements.settingsPage
    };

    // Hide all pages initially
    Object.values(pageElements).forEach(page => {
        if (page) page.style.display = 'none';
    });
    // Show overview page and set active navigation item
    if (pageElements.overview) {
        pageElements.overview.style.display = 'block';
        document.querySelector('.nav-item[data-section="overview"]').classList.add('active');
        document.querySelector('.main-content .header h2').textContent = "网络总览";
    } else {
        console.error("Overview page element not found!");
    }

    // Add click listeners to navigation items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');
            
            // Remove active class from all nav items and add to the clicked one
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Hide all pages
            Object.values(pageElements).forEach(page => {
                if (page) page.style.display = 'none';
            });
            
            // Show the selected page
            const currentPage = pageElements[section];
            if (currentPage) {
                currentPage.style.display = 'block';
                // Update header title based on current page
                const sectionTitle = this.querySelector('span').textContent;
                document.querySelector('.main-content .header h2').textContent = sectionTitle;

                // Special handling for specific pages
                if (section === 'blocks') {
                    if (elements.blocksTreeContainer) {
                        fetchAndRenderBlocksTree(); // Call the passed function to load the tree
                    } else {
                        console.error("Block tree container not found for section 'blocks'");
                    }
                } else if (section === 'outbox') { 
                    if (initializeOutboxDetailedView) { 
                        initializeOutboxDetailedView(elements); 
                    } else {
                        console.error("initializeOutboxDetailedView function not passed or found.");
                    }
                } else if (section === 'orphan-blocks') { // <-- 新增：处理孤儿块页面激活
                    if (initializeOrphanBlocksPage) {
                        initializeOrphanBlocksPage(elements);
                    } else {
                        console.error("initializeOrphanBlocksPage function not passed or found.");
                    }
                }
            } else {
                console.warn(`Page element for section '${section}' not found.`);
            }
        });
    });
}

/**
 * Updates the peers table and related stats on the dashboard.
 * @param {Array<object>} peers - Array of peer data.
 * @param {object} elements - Object containing references to DOM elements.
 */
export function updatePeersUI(peers, elements) {
    if (!Array.isArray(peers)) {
        console.error("Peers data is not an array:", peers);
        elements.peersTable.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--danger);">节点数据格式错误</td></tr>';
        elements.activePeers.textContent = "错误";
        return;
    }
    const activePeersCount = peers.filter(p => p.status === 'ALIVE' || p.status === 'MYSELF').length;
    elements.activePeers.textContent = activePeersCount;
    elements.peersProgress.style.width = `${Math.min(100, activePeersCount / (peers.length || 1) * 100)}%`; 
    
    let tableHTML = '';
    peers.forEach(peer => {
        const shortId = peer.peer_id && peer.peer_id.length > 15 ? 
            peer.peer_id.substr(0, 6) + '...' + peer.peer_id.substr(-6) : 
            (peer.peer_id || '未知ID');
        
        let statusClass = 'status-offline'; let statusText = peer.status || '未知';
        if (peer.status === 'ALIVE') statusClass = 'status-online';
        else if (peer.status === 'MYSELF') statusClass = 'status-syncing';
        
        let latencyClass = 'latency-high';
        if (peer.latency < 100) latencyClass = 'latency-low';
        else if (peer.latency < 200) latencyClass = 'latency-medium';
        
        const peerTypeClass = peer.type === 'lightweight' ? 'peer-light' : 'peer-full';
        const peerTypeText = peer.type === 'lightweight' ? '轻节点' : '全节点';
        
        const natStatusText = peer.NATed ? '已启用' : '未启用';
        const natClass = peer.NATed ? 'status-warning' : 'status-success'; 
        
        tableHTML += `
        <tr>
            <td title="${peer.peer_id || ''}">${shortId}</td>
            <td>${peer.ip || 'N/A'}</td>
            <td>${peer.port || 'N/A'}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td><span class="latency-indicator ${latencyClass}"></span> ${peer.latency != null ? peer.latency + ' ms' : 'N/A'}</td>
            <td><span class="peer-type ${peerTypeClass}">${peerTypeText}</span></td>
            <td><span class="status-badge ${natClass}">${natStatusText}</span></td>
            <td>${peer.localnetworkid || 'N/A'}</td>
        </tr>`;
    });
    elements.peersTable.innerHTML = tableHTML || '<tr><td colspan="8" style="text-align: center;">无节点数据</td></tr>';
}

/**
 * Updates the latest blocks list on the overview page.
 * @param {Array<object>} latestBlocksFlat - Flat, sorted array of block data.
 * @param {object} elements - Object containing references to DOM elements.
 */
export function updateBlocksUI(latestBlocksFlat, elements) {
    if (!Array.isArray(latestBlocksFlat)) {
         console.error("Latest blocks data is not an array:", latestBlocksFlat);
         elements.blocksList.innerHTML = '<div class="block-row"><div class="block-icon"><i class="fas fa-exclamation-circle"></i></div><div class="block-info"><div>区块数据格式错误</div></div></div>';
         return;
    }

    const totalBlockCount = latestBlocksFlat.length; 
    elements.blockCountStat.textContent = totalBlockCount;
    elements.blockHeightSysInfo.textContent = `#${totalBlockCount}`;
    elements.blocksProgress.style.width = `${Math.min(100, (totalBlockCount % 1000) / 10)}%`; 

    let blocksHTML = '';
    latestBlocksFlat.slice(0, 5).forEach(block => { 
        const blockHashShort = block.hash ? 
            block.hash.substr(0, 8) + '...' + block.hash.substr(-8) : 
            '未知哈希';
        const txCount = block.transactions ? block.transactions.length : 0;
        const timeAgo = block.timestamp ? formatTimeAgo(block.timestamp * 1000) : "未知时间"; 
        
        blocksHTML += `
        <div class="block-row">
            <div class="block-icon"><i class="fas fa-cube"></i></div>
            <div class="block-info">
                <div>区块 <span class="block-hash" title="${block.hash || ''}">${blockHashShort}</span></div>
                <div>${txCount} 笔交易 | ${timeAgo}</div>
            </div>
        </div>`;
    });
    elements.blocksList.innerHTML = blocksHTML || '<div class="block-row"><div class="block-icon"><i class="fas fa-cube"></i></div><div class="block-info"><div>无区块数据</div></div></div>';
}

/**
 * Updates the network throughput display and its progress bar.
 * @param {number} throughputValue - The current network throughput in MB/s.
 * @param {object} elements - Object containing references to DOM elements.
 */
export function updateNetworkThroughputUI(throughputValue, elements) {
    elements.networkThroughput.textContent = `${throughputValue.toFixed(1)} MB/s`;
    elements.throughputProgress.style.width = `${Math.min(100, throughputValue / 50 * 100)}%`; 
}

/**
 * Updates the transactions table and pending transactions stat.
 * @param {Array<object>} transactions - Array of transaction data.
 * @param {object} elements - Object containing references to DOM elements.
 */
export function updateTransactionsUI(transactions, elements) {
    if (!Array.isArray(transactions)) {
        console.error("Transactions data is not an array:", transactions);
        elements.transactionsTable.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--danger);">交易数据格式错误</td></tr>';
        elements.pendingTxs.textContent = "错误";
        return;
    }
    const pendingTxsCount = transactions.length;

    elements.pendingTxs.textContent = pendingTxsCount;
    elements.txsProgress.style.width = `${Math.min(100, pendingTxsCount / (transactions.length || 1) * 100)}%`;

    let tableHTML = '';
    transactions.slice(0, 5).forEach(tx => {
        const txIdShort = tx.id ? tx.id.substr(0, 8) + '...' + tx.id.substr(-8) : '未知ID';
        const amount = tx.amount != null ? `${tx.amount} ETH` : '未知金额';
        let statusClass = 'status-syncing'; 
        let statusText = '待处理';

        tableHTML += `
        <tr>
            <td title="${tx.id || ''}">${txIdShort}</td>
            <td>${amount}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        </tr>`;
    });
    elements.transactionsTable.innerHTML = tableHTML || '<tr><td colspan="3" style="text-align: center;">无交易数据</td></tr>';
}
/**
 * Updates the outbox (message queue) table on the OVERVIEW page.
 * This function is specifically for the summary table.
 * @param {object} outboxDataContainer - Object containing outbox data.
 * @param {object} elements - Object containing references to DOM elements.
 */
export function updateOutboxUI(outboxDataContainer, elements) {
    // 确保 outboxDataContainer 和 outboxDataContainer.data 存在
    const outbox = outboxDataContainer ? outboxDataContainer.data : null;
    if (!outbox || typeof outbox !== 'object') {
         console.error("Outbox data is not in the expected format:", outboxDataContainer);
         elements.outboxTable.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--danger);">消息队列数据格式错误</td></tr>';
         return;
    }
    
    let tableHTML = '';
    let totalPendingMessages = 0; 

    // 遍历 outbox 对象中的每个 peer_id 及其消息数据，仅显示前5个peer的摘要
    Object.entries(outbox).slice(0, 5).forEach(([peerId, prioritiesMap]) => { 
        const shortId = peerId.length > 15 ? peerId.substr(0, 6) + '...' + peerId.substr(-6) : peerId;
        
        const highCount = (prioritiesMap && prioritiesMap.high) ? prioritiesMap.high.length : 0;
        const mediumCount = (prioritiesMap && prioritiesMap.medium) ? prioritiesMap.medium.length : 0;
        const lowCount = (prioritiesMap && prioritiesMap.low) ? prioritiesMap.low.length : 0;
        const totalMessages = highCount + mediumCount + lowCount;
        
        totalPendingMessages += totalMessages; 

        let priorityClass = 'priority-medium'; 
        let priorityText = '中';

        if (highCount > 0) { 
            priorityClass = 'priority-high'; 
            priorityText = '高'; 
        } else if (mediumCount > 0) {
            priorityClass = 'priority-medium'; 
            priorityText = '中';
        } else if (lowCount > 0) { 
            priorityClass = 'priority-low'; 
            priorityText = '低';
        } else {
            priorityClass = ''; 
            priorityText = '无';
        }
        
        tableHTML += `
        <tr>
            <td title="${peerId}">${shortId}</td>
            <td><span class="queue-priority ${priorityClass}">${priorityText}</span></td>
            <td>${totalMessages}</td>
        </tr>`;
    });

    elements.pendingTxs.textContent = totalPendingMessages; 
    elements.txsProgress.style.width = `${Math.min(100, totalPendingMessages / 100 * 100)}%`; 

    elements.outboxTable.innerHTML = tableHTML || '<tr><td colspan="3" style="text-align: center;">无待发送消息</td></tr>';
}


/**
 * Initializes the dedicated Outbox (消息队列) page with a detailed message view.
 * This function fetches outbox data, populates the peer dropdown, and renders messages for the first peer.
 * @param {object} elements - Object containing references to DOM elements.
 */
export async function initializeOutboxDetailedView(elements) {
    // 使用新的 ID
    const peerSelectElement = elements.outboxPeerSelect;
    const messageListContainerElement = elements.outboxMessageListContainer;

    if (!peerSelectElement || !messageListContainerElement) {
        console.error("Outbox detailed view DOM elements not found.");
        return;
    }

    messageListContainerElement.innerHTML = '<div class="empty-message">加载消息详情中...</div>';
    peerSelectElement.innerHTML = '<option value="">加载中...</option>';
    peerSelectElement.disabled = true;

    try {
        const outboxDataContainer = await fetchOutboxData();
        const outbox = outboxDataContainer ? outboxDataContainer.data : null;

        if (!outbox || Object.keys(outbox).length === 0) {
            messageListContainerElement.innerHTML = '<div class="empty-message">无待发送消息数据。</div>';
            peerSelectElement.innerHTML = '<option value="">无节点</option>';
            peerSelectElement.disabled = true;
            return;
        }

        // Populate peer dropdown
        peerSelectElement.innerHTML = '';
        const peerIds = Object.keys(outbox).sort(); // 按字母顺序排序
        peerIds.forEach(peerId => {
            const option = document.createElement('option');
            option.value = peerId;
            option.textContent = peerId;
            peerSelectElement.appendChild(option);
        });
        peerSelectElement.disabled = false;

        // Add event listener for dropdown change
        peerSelectElement.onchange = () => {
            renderSelectedPeerMessages(elements, outbox);
        };

        // Render messages for the initially selected peer
        renderSelectedPeerMessages(elements, outbox);

    } catch (error) {
        console.error('Failed to initialize outbox detailed view:', error);
        messageListContainerElement.innerHTML = `<div class="empty-message" style="color: var(--danger);">加载消息详情失败: ${error.message}</div>`;
        peerSelectElement.innerHTML = '<option value="">加载失败</option>';
        peerSelectElement.disabled = true;
    }
}

/**
 * Renders messages for the currently selected peer in the message details panel.
 * @param {object} elements - Object containing references to DOM elements.
 * @param {object} allOutboxData - The full outbox data object.
 */
function renderSelectedPeerMessages(elements, allOutboxData) {
    // 使用新的 ID
    const selectedPeerId = elements.outboxPeerSelect.value;
    const messageListContainerElement = elements.outboxMessageListContainer;

    const messagesForPeer = allOutboxData[selectedPeerId];

    messageListContainerElement.innerHTML = ''; // Clear previous messages

    if (!messagesForPeer || Object.keys(messagesForPeer).length === 0) {
        messageListContainerElement.innerHTML = '<div class="empty-message">该节点无待发送消息。</div>';
        return;
    }

    const priorityOrder = ['high', 'medium', 'low']; // 定义优先级顺序

    priorityOrder.forEach(priority => {
        const messages = messagesForPeer[priority];
        if (messages && messages.length > 0) {
            const priorityHeader = document.createElement('h3');
            priorityHeader.className = 'message-priority-group';
            priorityHeader.textContent = `${priority.charAt(0).toUpperCase() + priority.slice(1)} 优先级消息 (${messages.length})`;
            messageListContainerElement.appendChild(priorityHeader);

            messages.forEach((msgArray, index) => {
                try {
                    // msgArray 是 [json_string, ip, port]
                    const messageJsonStr = msgArray[0];
                    const targetIp = msgArray[1];
                    const targetPort = msgArray[2];
                    
                    const message = JSON.parse(messageJsonStr);
                    renderMessageCard(message, targetIp, targetPort, messageListContainerElement, priority);
                } catch (e) {
                    console.error('Error parsing message JSON:', e, msgArray);
                    const errorCard = document.createElement('div');
                    errorCard.className = 'message-card';
                    errorCard.innerHTML = `<div class="message-header">
                                                <div class="toggle-icon"><i class="fas fa-exclamation-triangle"></i></div>
                                                <div class="message-type" style="color: var(--danger);">解析错误</div>
                                                <div class="message-id">${msgArray[0].substring(0, 50)}...</div>
                                            </div>
                                            <div class="message-content" style="display: block;">
                                                <p style="color: var(--danger);">无法解析消息: ${e.message}</p>
                                                <p>原始数据: ${JSON.stringify(msgArray)}</p>
                                            </div>`;
                    messageListContainerElement.appendChild(errorCard);
                }
            });
        }
    });

    if (messageListContainerElement.innerHTML === '') {
        messageListContainerElement.innerHTML = '<div class="empty-message">该节点无待发送消息。</div>';
    }
}

/**
 * Renders a single message as an expandable card.
 * @param {object} message - The parsed message object.
 * @param {string} targetIp - The target IP for the message.
 * @param {number} targetPort - The target Port for the message.
 * @param {HTMLElement} container - The DOM element to append the card to.
 * @param {string} priority - The priority of the message ('high', 'medium', 'low').
 */
function renderMessageCard(message, targetIp, targetPort, container, priority) {
    const card = document.createElement('div');
    card.className = 'message-card';

    const header = document.createElement('div');
    header.className = 'message-header';
    card.appendChild(header);

    const toggleIcon = document.createElement('div');
    toggleIcon.className = 'toggle-icon';
    toggleIcon.innerHTML = '<i class="fas fa-plus"></i>'; // Default to plus
    header.appendChild(toggleIcon);

    const messageType = document.createElement('div');
    messageType.className = 'message-type';
    messageType.textContent = message.type || '未知类型';
    header.appendChild(messageType);

    const messageId = document.createElement('div');
    messageId.className = 'message-id';
    messageId.textContent = `ID: ${message.message_id ? message.message_id.substring(0, 12) + '...' : 'N/A'}`;
    messageId.title = message.message_id || 'N/A';
    header.appendChild(messageId);

    const content = document.createElement('div');
    content.className = 'message-content';
    card.appendChild(content);

    // Add common message details
    content.innerHTML += `
        <div class="message-details-row">
            <span class="message-details-label">目标:</span>
            <span class="message-details-value">${targetIp}:${targetPort}</span>
        </div>
        <div class="message-details-row">
            <span class="message-details-label">发送者:</span>
            <span class="message-details-value">${message.sender || 'N/A'}</span>
        </div>
        <div class="message-details-row">
            <span class="message-details-label">优先级:</span>
            <span class="message-details-value">${priority.charAt(0).toUpperCase() + priority.slice(1)}</span>
        </div>
    `;

    // Display all message properties as JSON for full detail
    const messageDetailsRow = document.createElement('div');
    messageDetailsRow.className = 'message-details-row';
    messageDetailsRow.innerHTML = `<span class="message-details-label">完整消息:</span><pre class="message-details-value json-pretty">${JSON.stringify(message, null, 2)}</pre>`;
    content.appendChild(messageDetailsRow);


    header.addEventListener('click', () => {
        const isVisible = content.style.display === 'block';
        content.style.display = isVisible ? 'none' : 'block';
        toggleIcon.innerHTML = isVisible ? '<i class="fas fa-plus"></i>' : '<i class="fas fa-minus"></i>';
    });

    container.appendChild(card);
}

/**
 * Initializes the Orphan Blocks page: fetches data and renders the list of orphan blocks.
 * @param {object} elements - Object containing references to DOM elements.
 */
export async function initializeOrphanBlocksPage(elements) {
    const container = elements.orphanBlocksListContainer;
    if (!container) {
        console.error("Orphan blocks list container not found in DOM.");
        return;
    }

    container.innerHTML = `<div class="loading-block">
                            <div class="block-row">
                                <div class="block-icon"><i class="fas fa-cube"></i></div>
                                <div class="block-info"><div>加载孤儿块数据中...</div></div>
                            </div>
                          </div>`;
    try {
        const orphanBlocksData = await fetchOrphanBlocksData();
        renderOrphanBlocks(orphanBlocksData, container);
    } catch (error) {
        console.error('获取孤儿块数据失败:', error);
        container.innerHTML = `<div class="empty-message">无法加载孤儿块数据. Error: ${error.message}</div>`;
    }
}

/**
 * Renders the list of orphan blocks.
 * @param {Array<object>} orphanBlocks - Array of orphan block data.
 * @param {HTMLElement} container - The DOM element to render the blocks into.
 */
function renderOrphanBlocks(orphanBlocks, container) {
    if (!Array.isArray(orphanBlocks) || orphanBlocks.length === 0) {
        container.innerHTML = '<div class="empty-message">无孤儿块数据。</div>';
        return;
    }

    container.innerHTML = ''; // Clear previous content

    orphanBlocks.forEach(orphanBlock => {
        const blockNode = document.createElement('div');
        blockNode.className = 'block-node'; // 复用 blockTree 的样式

        const blockHeader = document.createElement('div');
        blockHeader.className = 'block-header';
        blockNode.appendChild(blockHeader);

        const toggleIcon = document.createElement('div');
        toggleIcon.className = 'toggle-icon';
        toggleIcon.innerHTML = '<i class="fas fa-plus"></i>'; // 默认折叠
        blockHeader.appendChild(toggleIcon);

        const indicator = document.createElement('div');
        indicator.className = 'block-indicator';
        indicator.style.backgroundColor = 'var(--danger)'; // 孤儿块用红色指示
        blockHeader.appendChild(indicator);

        const blockInfo = document.createElement('div');
        blockInfo.className = 'block-info';
        blockHeader.appendChild(blockInfo);

        const blockId = document.createElement('div');
        blockId.className = 'block-id';
        blockId.textContent = `孤儿块 ID: ${orphanBlock.block_id ? orphanBlock.block_id.substring(0,12) + '...' : 'N/A'}`;
        blockId.title = orphanBlock.block_id || 'N/A';
        blockInfo.appendChild(blockId);
        
        const prevIdDisplay = (orphanBlock.prev_id === "0000000000000000000000000000000000000000000000000000000000000000" || orphanBlock.prev_id === "000000") 
                                ? '创世块' 
                                : (orphanBlock.prev_id ? orphanBlock.prev_id.substring(0,12) + '...' : 'N/A');

        const blockHash = document.createElement('div'); 
        blockHash.className = 'block-hash'; 
        blockHash.textContent = `父区块: ${prevIdDisplay}`;
        blockHash.title = orphanBlock.prev_id || 'N/A';
        blockInfo.appendChild(blockHash);

        const detailsContainer = document.createElement('div');
        detailsContainer.className = 'block-details'; // 复用 blockTree 的样式
        detailsContainer.style.display = 'none'; // 默认隐藏
        blockNode.appendChild(detailsContainer);

        // Add details for orphan block
        const timestampInfo = document.createElement('div');
        timestampInfo.className = 'detail-row';
        const time = orphanBlock.timestamp ? new Date(orphanBlock.timestamp * 1000).toLocaleString() : 'N/A';
        timestampInfo.innerHTML = `<span class="detail-label">时间:</span><span class="detail-value">${time}</span>`;
        detailsContainer.appendChild(timestampInfo);

        const txCountInfo = document.createElement('div');
        txCountInfo.className = 'detail-row';
        txCountInfo.innerHTML = `<span class="detail-label">交易数:</span><span class="detail-value">${orphanBlock.tx_count != null ? orphanBlock.tx_count : 'N/A'}</span>`;
        detailsContainer.appendChild(txCountInfo);

        // Add click event listener to toggle details
        blockHeader.addEventListener('click', function() {
            const isVisible = detailsContainer.style.display === 'block';
            detailsContainer.style.display = isVisible ? 'none' : 'block';
            toggleIcon.innerHTML = isVisible ? '<i class="fas fa-plus"></i>' : '<i class="fas fa-minus"></i>';
        });

        container.appendChild(blockNode);
    });
}

/**
 * Formats a timestamp into a human-readable "time ago" string.
 * @param {number} timestamp - The timestamp in milliseconds.
 * @returns {string} - The formatted time ago string.
 */
export function formatTimeAgo(timestamp) {
    const now = Date.now();
    const seconds = Math.round((now - timestamp) / 1000);

    if (seconds < 5) return `刚刚`;
    if (seconds < 60) return `${seconds} 秒前`;
    
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} 分钟前`;
    
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    
    const days = Math.round(hours / 24);
    return `${days} 天前`;
}