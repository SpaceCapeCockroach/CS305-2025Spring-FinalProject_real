// chart.js
let networkChart;
let chartMode = 'latency'; // 'latency' or 'throughput'
let latencyDataPoints = []; // Stores raw latency data points for aggregation
let throughputDataPoints = []; // Stores raw throughput data points for aggregation

/**
 * Initializes the Chart.js instance for network performance.
 * @param {HTMLCanvasElement} canvasElement - The canvas DOM element where the chart will be rendered.
 */
export function initNetworkChart(canvasElement) {
    const ctx = canvasElement.getContext('2d');
    const rootStyles = getComputedStyle(document.documentElement);

    networkChart = new Chart(ctx, {
        type: 'line',
        data: {
            // Initialize labels for the last 12 intervals (e.g., 30 seconds apart)
            labels: Array(12).fill("").map((_, i) => { 
                const d = new Date(Date.now() - (11-i) * 30000); // Backwards in time
                return `${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
            }),
            datasets: [{
                label: '平均延迟 (ms)',
                data: [], // Initial empty data
                borderColor: rootStyles.getPropertyValue('--highlight').trim(),
                backgroundColor: 'rgba(233, 69, 96, 0.1)', 
                tension: 0.4, // Smooth curve
                fill: true,
                pointRadius: 3,
                pointBackgroundColor: rootStyles.getPropertyValue('--highlight').trim()
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { 
                    labels: { 
                        color: rootStyles.getPropertyValue('--text').trim() // Legend text color
                    } 
                } 
            },
            scales: {
                x: { 
                    grid: { color: rootStyles.getPropertyValue('--border').trim() }, // X-axis grid color
                    ticks: { color: rootStyles.getPropertyValue('--text-secondary').trim(), maxRotation: 30, minRotation: 30 } // X-axis tick color
                },
                y: { 
                    grid: { color: rootStyles.getPropertyValue('--border').trim() }, // Y-axis grid color
                    ticks: { color: rootStyles.getPropertyValue('--text-secondary').trim() }, // Y-axis tick color
                    beginAtZero: true 
                }
            }
        }
    });
}

/**
 * Sets the chart display mode (latency or throughput) and updates button styles.
 * @param {string} mode - The desired chart mode ('latency' or 'throughput').
 * @param {HTMLElement} latencyBtn - The DOM element for the latency button.
 * @param {HTMLElement} throughputBtn - The DOM element for the throughput button.
 */
export function setChartMode(mode, latencyBtn, throughputBtn) {
    chartMode = mode;
    latencyBtn.classList.toggle('active', mode === 'latency');
    throughputBtn.classList.toggle('active', mode === 'throughput');
    updateChartData(); // Force chart update to reflect the new mode immediately
}

/**
 * Updates the chart's data and labels based on the current chart mode and new data points.
 * This function is called periodically to append new data.
 * @param {Array<number>} newLatencyData - An array of new latency values (in ms) to add.
 * @param {Array<number>} newThroughputData - An array of new throughput values (in MB/s) to add.
 */
export function updateChartData(newLatencyData = [], newThroughputData = []) {
    if (!networkChart) return; // Ensure chart is initialized

    // Accumulate new data points into internal arrays
    latencyDataPoints.push(...newLatencyData);
    throughputDataPoints.push(...newThroughputData);

    const rootStyles = getComputedStyle(document.documentElement);
    const now = new Date();
    // Generate a new label for the current time point
    const newLabel = `${now.getHours()}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;

    // Shift labels if the chart has reached its maximum data points
    if (networkChart.data.labels.length >= 12) {
        networkChart.data.labels.shift();
    }
    networkChart.data.labels.push(newLabel); // Add the new label

    if (chartMode === 'latency') {
        // Calculate average latency from accumulated points
        const avgLatency = latencyDataPoints.length > 0 ? latencyDataPoints.reduce((a,b)=>a+b,0) / latencyDataPoints.length : 0;
        if (networkChart.data.datasets[0].data.length >= 12) {
            networkChart.data.datasets[0].data.shift();
        }
        networkChart.data.datasets[0].data.push(avgLatency); // Add the new data point
        networkChart.data.datasets[0].label = '平均延迟 (ms)';
        networkChart.data.datasets[0].borderColor = rootStyles.getPropertyValue('--highlight').trim();
        networkChart.data.datasets[0].backgroundColor = 'rgba(233, 69, 96, 0.1)';
        networkChart.data.datasets[0].pointBackgroundColor = rootStyles.getPropertyValue('--highlight').trim();
        latencyDataPoints = []; // Clear accumulated points for the next interval
    } else { // chartMode === 'throughput'
        // Calculate average throughput from accumulated points
        const avgThroughput = throughputDataPoints.length > 0 ? throughputDataPoints.reduce((a,b)=>a+b,0) / throughputDataPoints.length : 0;
         if (networkChart.data.datasets[0].data.length >= 12) {
            networkChart.data.datasets[0].data.shift();
        }
        networkChart.data.datasets[0].data.push(avgThroughput); // Add the new data point
        networkChart.data.datasets[0].label = '吞吐量 (MB/s)';
        networkChart.data.datasets[0].borderColor = rootStyles.getPropertyValue('--success').trim();
        networkChart.data.datasets[0].backgroundColor = 'rgba(74, 222, 128, 0.1)';
        networkChart.data.datasets[0].pointBackgroundColor = rootStyles.getPropertyValue('--success').trim();
        throughputDataPoints = []; // Clear accumulated points for the next interval
    }
    networkChart.update('none'); // Update the chart without animation
}