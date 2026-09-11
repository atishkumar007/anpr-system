let trafficChartInstance = null;
let statusChartInstance = null;

function initCharts() {
    // 1. Hourly Traffic Line/Bar Chart
    const ctxTraffic = document.getElementById('trafficHourlyChart');
    if (ctxTraffic) {
        trafficChartInstance = new Chart(ctxTraffic, {
            type: 'bar',
            data: {
                labels: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`),
                datasets: [
                    {
                        label: 'Authorized',
                        data: new Array(24).fill(0),
                        backgroundColor: 'rgba(16, 185, 129, 0.7)',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Unauthorized / Blocked',
                        data: new Array(24).fill(0),
                        backgroundColor: 'rgba(239, 68, 68, 0.7)',
                        borderColor: '#ef4444',
                        borderWidth: 1,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        ticks: { color: '#64748b', maxTicksLimit: 12 },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: { color: '#64748b', stepSize: 1 },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                }
            }
        });
    }

    // 2. Status Doughnut Chart
    const ctxStatus = document.getElementById('statusRatioChart');
    if (ctxStatus) {
        statusChartInstance = new Chart(ctxStatus, {
            type: 'doughnut',
            data: {
                labels: ['Authorized', 'Unauthorized', 'Blacklisted'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } }
                    }
                },
                cutout: '70%'
            }
        });
    }
}

async function updateChartsData() {
    try {
        // Fetch stats summary
        const resStats = await fetch('/api/logs/stats');
        if (resStats.ok) {
            const stats = await resStats.json();
            if (statusChartInstance) {
                statusChartInstance.data.datasets[0].data = [
                    stats.authorized_count,
                    stats.unauthorized_count,
                    stats.blacklisted_count
                ];
                statusChartInstance.update();
            }
        }

        // Fetch hourly analytics
        const resHourly = await fetch('/api/logs/analytics/hourly');
        if (resHourly.ok) {
            const hourly = await resHourly.json();
            const hours = Object.keys(hourly);
            const authCounts = hours.map(h => hourly[h].authorized || 0);
            const unauthCounts = hours.map(h => (hourly[h].unauthorized || 0) + (hourly[h].blacklisted || 0));

            if (trafficChartInstance) {
                trafficChartInstance.data.labels = hours;
                trafficChartInstance.data.datasets[0].data = authCounts;
                trafficChartInstance.data.datasets[1].data = unauthCounts;
                trafficChartInstance.update();
            }
        }
    } catch (err) {
        console.error("Failed to refresh chart data:", err);
    }
}

window.initCharts = initCharts;
window.updateChartsData = updateChartsData;
