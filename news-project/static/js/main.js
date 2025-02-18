document.addEventListener("DOMContentLoaded", () => {
    try {
        // Parse JSON data
        const sentimentData = JSON.parse(document.getElementById('sentiment-data')?.textContent || '{"labels": [], "data": []}');
        const keywordData = JSON.parse(document.getElementById('keyword-data')?.textContent || '{"labels": [], "data": []}');
        const trendData = JSON.parse(document.getElementById('trend-data')?.textContent || '{"labels": [], "data": []}');
        const categoryData = JSON.parse(document.getElementById('category-data')?.textContent || '{"labels": [], "data": []}');
        const channelData = JSON.parse(document.getElementById('channel-data')?.textContent || '{"labels": [], "positive": [], "neutral": [], "negative": []}');

        console.log("Sentiment Data:", sentimentData);
        console.log("Keyword Data:", keywordData);
        console.log("Trend Data:", trendData);
        console.log("Category Data:", categoryData);
        console.log("Channel Data:", channelData);

        // Chart options
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top' },
            },
        };

        // Sentiment Chart
        if (sentimentData.labels.length > 0) {
            const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
            new Chart(sentimentCtx, {
                type: 'pie',
                data: {
                    labels: sentimentData.labels,
                    datasets: [{
                        data: sentimentData.data,
                        backgroundColor: ['#4caf50', '#f44336', '#ffeb3b'],
                    }],
                },
                options: chartOptions,
            });
        }

        // Keywords Chart
        if (keywordData.labels.length > 0) {
            const keywordCtx = document.getElementById('keywordChart').getContext('2d');
            new Chart(keywordCtx, {
                type: 'bar',
                data: {
                    labels: keywordData.labels,
                    datasets: [{
                        label: 'Frequency',
                        data: keywordData.data,
                        backgroundColor: '#2196f3',
                    }],
                },
                options: chartOptions,
            });
        }

        // Trend Chart
        if (trendData.labels.length > 0) {
            const trendCtx = document.getElementById('trendChart').getContext('2d');
            new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: trendData.labels,
                    datasets: [{
                        label: 'Analyses',
                        data: trendData.data,
                        borderColor: '#9c27b0',
                        fill: false,
                    }],
                },
                options: chartOptions,
            });
        }

        // Category Chart
        if (categoryData.labels.length > 0) {
            const categoryCtx = document.getElementById('categoryChart').getContext('2d');
            new Chart(categoryCtx, {
                type: 'bar',
                data: {
                    labels: categoryData.labels,
                    datasets: [{
                        label: 'Count',
                        data: categoryData.data,
                        backgroundColor: ['#ff5722', '#00bcd4', '#8bc34a', '#ffc107'],
                    }],
                },
                options: chartOptions,
            });
        }

        // Channel Comparison Chart
        if (channelData.labels.length > 0) {
            const channelCtx = document.getElementById('channelChart').getContext('2d');
            new Chart(channelCtx, {
                type: 'bar',
                data: {
                    labels: channelData.labels,
                    datasets: [
                        {
                            label: 'Positive',
                            data: channelData.positive,
                            backgroundColor: '#4caf50',
                        },
                        {
                            label: 'Neutral',
                            data: channelData.neutral,
                            backgroundColor: '#ffeb3b',
                        },
                        {
                            label: 'Negative',
                            data: channelData.negative,
                            backgroundColor: '#f44336',
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true, position: 'top' },
                    },
                    scales: {
                        x: { stacked: true },
                        y: { stacked: true, beginAtZero: true },
                    },
                },
            });
        }
    } catch (error) {
        console.error("Error initializing charts:", error);
    }
});
