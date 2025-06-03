// dashboard.js
// Global variables for the application state
export let peerId = "0x" + Math.random().toString(16).substr(2, 12);
export let startTime = Date.now();
export let elements; 

// Import functions from other modules
import { fetchPeersData, fetchBlocksData, fetchTransactionsData, fetchOutboxData, fetchNetworkPerformanceRawData, fetchOrphanBlocksData, fetchBlacklistData } from './api.js'; // <-- 新增 fetchBlacklistData
import { initUI, updateUptime, updatePeersUI, updateBlocksUI, updateTransactionsUI, updateOutboxUI, setupPageNavigationUI, updateNetworkThroughputUI, initializeOutboxDetailedView, initializeOrphanBlocksPage, updateBlacklistUI, initializeBlacklistPage } from './ui.js'; // <-- 新增 updateBlacklistUI, initializeBlacklistPage
// <-- 关键修改：chart.js 的导入，不再需要 setChartMode
import { initNetworkChart, updateChartData } from './chart.js'; 
import { renderBlockTree, extractAndSortBlocksFromTree } from './blockTree.js';

/**
 * Fetches all dashboard data concurrently and updates the UI.
 */
async function fetchDashboardData() {
    // Fetch all data concurrently
    const [peers, blocksTree, transactions, outbox, networkPerf] = await Promise.all([
        fetchPeersData(),
        fetchBlocksData(),
        fetchTransactionsData(),
        fetchOutboxData(),
        fetchNetworkPerformanceRawData()
    ]);

    // Update UI with fetched data
    if (peers) updatePeersUI(peers, elements);
    if (blocksTree) {
        const sortedFlatBlocks = extractAndSortBlocksFromTree(blocksTree);
        updateBlocksUI(sortedFlatBlocks, elements);
    }
    if (transactions) updateTransactionsUI(transactions, elements);
    if (outbox) updateOutboxUI(outbox, elements); 
    if (networkPerf) {
        // 关键修改：只传递吞吐量数据给图表更新
        updateChartData(networkPerf.throughputData); 
        updateNetworkThroughputUI(networkPerf.throughputValue, elements);
    }
}

/**
 * Fetches and renders the block tree for the Block Explorer page.
 * This function is specifically called when the "区块浏览器" tab is clicked.
 */
async function fetchAndRenderBlocksTree() {
    const container = elements.blocksTreeContainer;
    if (!container) {
        console.error("Blocks tree container not found in DOM.");
        return;
    }
    // Show loading state
    container.innerHTML = `<div class="loading-block">
                            <div class="block-row">
                                <div class="block-icon"><i class="fas fa-cube"></i></div>
                                <div class="block-info"><div>加载区块树结构中...</div></div>
                            </div>
                          </div>`;
    try {
        const treeData = await fetchBlocksData();
        renderBlockTree(treeData, container);
    } catch (error) {
        console.error('获取区块树失败:', error);
        container.innerHTML = `<div class="empty-message">无法加载区块数据. Error: ${error.message}</div>`;
    }
}

// Initialize dashboard on DOMContentLoaded event
document.addEventListener('DOMContentLoaded', () => {
    // 在 DOMContentLoaded 内部初始化 elements 对象，确保所有 DOM 元素都已加载
    elements = {
        nodeId: document.getElementById('node-id'),
        blockHeightSysInfo: document.getElementById('block-height'),
        uptime: document.getElementById('uptime'),
        
        activePeers: document.getElementById('active-peers'),
        blockCountStat: document.getElementById('block-count'),
        pendingTxs: document.getElementById('pending-txs'),
        networkThroughput: document.getElementById('network-throughput'),
        peersProgress: document.getElementById('peers-progress'),
        blocksProgress: document.getElementById('blocks-progress'),
        txsProgress: document.getElementById('txs-progress'),
        throughputProgress: document.getElementById('throughput-progress'),
        
        blocksList: document.getElementById('blocks-list'),
        peersTable: document.getElementById('peers-table'),
        transactionsTable: document.getElementById('transactions-table'),
        outboxTable: document.getElementById('outbox-table'), 
        
        refreshBlocksBtn: document.getElementById('refresh-blocks'),
        refreshPeersBtn: document.getElementById('refresh-peers'),
        refreshTxsBtn: document.getElementById('refresh-txs'),
        refreshOutboxBtn: document.getElementById('refresh-outbox'), 
        refreshBlocksTreeBtn: document.getElementById('refresh-blocks-tree'),
        
        refreshOutboxDetailedViewBtn: document.getElementById('refresh-outbox-detailed-view'), 
        outboxPeerSelect: document.getElementById('outbox-peer-select'), 
        outboxMessageListContainer: document.getElementById('outbox-message-list-container'), 
        
        orphanBlocksPage: document.getElementById('orphan-blocks-page'),
        refreshOrphanBlocksBtn: document.getElementById('refresh-orphan-blocks'),
        orphanBlocksListContainer: document.getElementById('orphan-blocks-list-container'),
        
        // 关键修改：移除 latencyBtn
        // latencyBtn: document.getElementById('latency-btn'),
        throughputBtn: document.getElementById('throughput-btn'), // 吞吐量按钮保留
        
        overviewPage: document.getElementById('overview-page'),
        blocksPage: document.getElementById('blocks-page'),
        peersPage: document.getElementById('peers-page'),
        transactionsPage: document.getElementById('transactions-page'),
        performancePage: document.getElementById('performance-page'),
        outboxPage: document.getElementById('outbox-page'), 
        settingsPage: document.getElementById('settings-page'),
        // 新增黑名单页面元素
        blacklistPage: document.getElementById('blacklist-page'),
        refreshBlacklistBtn: document.getElementById('refresh-blacklist'),
        blacklistTable: document.getElementById('blacklist-table'),
        
        blocksTreeContainer: document.getElementById('blocks-tree-container'),
        searchInput: document.getElementById('search-input'),
        blockTreeSearchInput: document.getElementById('block-search-tree'),
        blockTreeSearchBtn: document.getElementById('search-block-btn-tree'),
        networkChart: document.getElementById('networkChart') 
    };

    // Initialize UI components by passing necessary elements and global state
    initUI(elements, peerId, startTime); 
    // 关键修改：初始化图表时，不再需要 setChartMode
    initNetworkChart(elements.networkChart); 
    // 关键修改：传递 initializeBlacklistPage 给 setupPageNavigationUI
    setupPageNavigationUI(elements, fetchAndRenderBlocksTree, initializeOutboxDetailedView, initializeOrphanBlocksPage, initializeBlacklistPage); 

    // Set up event listeners for refresh buttons
    elements.refreshBlocksBtn.addEventListener('click', () => fetchDashboardData().then(() => console.log('Blocks refreshed')));
    elements.refreshPeersBtn.addEventListener('click', async () => {
        const loadingIcon = elements.refreshPeersBtn.querySelector('.loading');
        loadingIcon.style.display = 'inline-block'; // Show loading spinner
        elements.refreshPeersBtn.disabled = true; // Disable button
        try {
            await fetchDashboardData(); // Fetch all data
            console.log('Peers refreshed');
        } finally {
            loadingIcon.style.display = 'none'; // Hide loading spinner
            elements.refreshPeersBtn.disabled = false; // Enable button
        }
    });
    elements.refreshTxsBtn.addEventListener('click', () => fetchDashboardData().then(() => console.log('Transactions refreshed')));
    elements.refreshOutboxBtn.addEventListener('click', () => fetchDashboardData().then(() => console.log('Outbox refreshed'))); 
    
    // 消息队列详细视图页面的刷新按钮监听器
    if (elements.refreshOutboxDetailedViewBtn) {
        elements.refreshOutboxDetailedViewBtn.addEventListener('click', () => initializeOutboxDetailedView(elements));
    }

    // Event listener for refreshing the block tree specifically
    if (elements.refreshBlocksTreeBtn) {
        elements.refreshBlocksTreeBtn.addEventListener('click', fetchAndRenderBlocksTree);
    }

    // 孤儿块页面的刷新按钮监听器
    if (elements.refreshOrphanBlocksBtn) {
        elements.refreshOrphanBlocksBtn.addEventListener('click', () => initializeOrphanBlocksPage(elements));
    }

    // 新增：黑名单页面的刷新按钮监听器
    if (elements.refreshBlacklistBtn) {
        elements.refreshBlacklistBtn.addEventListener('click', () => initializeBlacklistPage(elements));
    }

    // 关键修改：移除 latencyBtn 的事件监听器
    // if (elements.latencyBtn) {
    //     elements.latencyBtn.addEventListener('click', () => setChartMode('latency', elements.latencyBtn, elements.throughputBtn));
    // }
    // 吞吐量按钮的事件监听器，如果它是唯一的，可以简化或移除 setChartMode
    if (elements.throughputBtn) {
        elements.throughputBtn.addEventListener('click', () => updateChartData(elements.networkChart.data.datasets[0].data)); // 强制更新图表为吞吐量模式
    }


    // Global search input functionality
    if (elements.searchInput) { 
        elements.searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) alert(`全局搜索: ${query}`); 
            }
        });
    }

    // Block tree search input functionality
    if (elements.blockTreeSearchInput && elements.blockTreeSearchBtn) { 
        elements.blockTreeSearchBtn.addEventListener('click', () => {
            const query = elements.blockTreeSearchInput.value.trim();
            if (query) alert(`区块树搜索: ${query}`); 
        });
        elements.blockTreeSearchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                const query = elements.blockTreeSearchInput.value.trim();
                if (query) alert(`区块树搜索: ${query}`); 
            }
        });
    }

    // Initial data fetch when the dashboard loads
    fetchDashboardData();
    // Set up periodic data refresh for the overview page
    setInterval(fetchDashboardData, 30000); 
    // Update uptime display every minute
    setInterval(() => updateUptime(startTime, elements.uptime), 60000);
});