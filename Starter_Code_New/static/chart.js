// chart.js
let networkChart;
// 关键修改：不再需要 chartMode 或 latencyDataPoints
// let chartMode = 'latency'; // 'latency' or 'throughput'
// let latencyDataPoints = []; 
let throughputDataPoints = []; // 只保留吞吐量数据点

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
            labels: Array(12).fill("").map((_, i) => { 
                const d = new Date(Date.now() - (11-i) * 30000); 
                return `${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
            }),
            datasets: [{
                label: '吞吐量 (MB/s)', // 关键修改：默认只显示吞吐量
                data: [], 
                borderColor: rootStyles.getPropertyValue('--success').trim(), // 吞吐量使用绿色
                backgroundColor: 'rgba(74, 222, 128, 0.1)', 
                tension: 0.4,
                fill: true,
                pointRadius: 3,
                pointBackgroundColor: rootStyles.getPropertyValue('--success').trim()
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: rootStyles.getPropertyValue('--text').trim() } } },
            scales: {
                x: { 
                    grid: { color: rootStyles.getPropertyValue('--border').trim() }, 
                    ticks: { color: rootStyles.getPropertyValue('--text-secondary').trim(), maxRotation: 30, minRotation: 30 } 
                },
                y: { 
                    grid: { color: rootStyles.getPropertyValue('--border').trim() }, 
                    ticks: { color: rootStyles.getPropertyValue('--text-secondary').trim() }, 
                    beginAtZero: true 
                }
            }
        }
    });
}

/**
 * 关键修改：移除 setChartMode 函数，因为不再需要切换模式。
 * 如果您希望吞吐量按钮仍然能“刷新”图表，可以将其事件监听器直接绑定到 updateChartData。
 */
// export function setChartMode(mode, latencyBtn, throughputBtn) {
//     chartMode = mode;
//     latencyBtn.classList.toggle('active', mode === 'latency');
//     throughputBtn.classList.toggle('active', mode === 'throughput');
//     updateChartData(true); 
// }

/**
 * Updates the chart's data and labels, now specifically for throughput.
 * @param {Array<number>} newThroughputData - An array of new throughput values (in MB/s) to add.
 */
export function updateChartData(newThroughputData = []) { // 关键修改：只接受吞吐量数据
    if (!networkChart) return;

    throughputDataPoints.push(...newThroughputData);

    const now = new Date();
    const newLabel = `${now.getHours()}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;

    if (networkChart.data.labels.length >= 12) {
        networkChart.data.labels.shift();
    }
    networkChart.data.labels.push(newLabel);

    const avgThroughput = throughputDataPoints.length > 0 ? throughputDataPoints.reduce((a,b)=>a+b,0) / throughputDataPoints.length : 0;
     if (networkChart.data.datasets[0].data.length >= 12) {
        networkChart.data.datasets[0].data.shift();
    }
    networkChart.data.datasets[0].data.push(avgThroughput);
    // 关键修改：标签和颜色固定为吞吐量
    networkChart.data.datasets[0].label = '吞吐量 (MB/s)';
    const rootStyles = getComputedStyle(document.documentElement);
    networkChart.data.datasets[0].borderColor = rootStyles.getPropertyValue('--success').trim();
    networkChart.data.datasets[0].backgroundColor = 'rgba(74, 222, 128, 0.1)';
    networkChart.data.datasets[0].pointBackgroundColor = rootStyles.getPropertyValue('--success').trim();
    throughputDataPoints = []; 
    
    networkChart.update('none'); 
}