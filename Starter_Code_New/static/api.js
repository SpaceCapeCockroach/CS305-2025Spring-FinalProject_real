// api.js
/**
 * Generic helper function to fetch data from a given URL.
 * @param {string} url - The API endpoint URL.
 * @returns {Promise<any | null>} - A promise that resolves with the JSON data, or null if an error occurs.
 */
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} ${response.statusText} from ${url}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching data from ${url}:`, error);
        return null; // Return null to indicate failure, allowing the caller to handle it gracefully
    }
}

/**
 * Fetches peer data from the '/peers' endpoint.
 * @returns {Promise<Array<object> | null>} - A promise that resolves with an array of peer objects, or null.
 */
export async function fetchPeersData() {
    return fetchData('/peers');
}

/**
 * Fetches block data from the '/blocks' endpoint.
 * Assumes this endpoint returns a tree-like structure or an array of root blocks.
 * @returns {Promise<Array<object> | object | null>} - A promise that resolves with block data, or null.
 */
export async function fetchBlocksData() {
    return fetchData('/blocks');
}

/**
 * Fetches transaction data from the '/transactions' endpoint.
 * @returns {Promise<Array<object> | null>} - A promise that resolves with an array of transaction objects, or null.
 */
export async function fetchTransactionsData() {
    return fetchData('/transactions');
}

/**
 * Fetches outbox (message queue) data from the '/outbox' endpoint.
 * @returns {Promise<object | null>} - A promise that resolves with outbox data, or null.
 */
export async function fetchOutboxData() {
    return fetchData('/outbox');
}

/**
 * Fetches raw network performance data (latency and throughput).
 * @returns {Promise<{latencyData: Array<number>, throughputData: Array<number>, throughputValue: number}>}
 *          A promise that resolves with an object containing raw latency points, throughput points, and current throughput value.
 */
export async function fetchNetworkPerformanceRawData() {
    const latencyData = [];
    let throughputValue = 0;

    try {
        const [latencyRes, capacityRes] = await Promise.all([
            fetch('/latency'),
            fetch('/capacity')
        ]);

        if (latencyRes.ok) {
            const data = await latencyRes.json();
            // Assuming latency endpoint returns an array of { latency_ms: number }
            data.forEach(item => latencyData.push(item.latency_ms));
        } else {
            console.warn(`Failed to fetch latency: ${latencyRes.status}`);
        }

        if (capacityRes.ok) {
            const data = await capacityRes.json();
            // Assuming capacity endpoint returns { capacity: number }
            throughputValue = data.capacity;
        } else {
            console.warn(`Failed to fetch capacity: ${capacityRes.status}`);
        }
    } catch (error) {
        console.error('获取网络性能数据失败:', error);
    }
    // Return the raw data for chart.js and ui.js to process
    return { latencyData, throughputData: [throughputValue], throughputValue };
}