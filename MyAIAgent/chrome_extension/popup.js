document.addEventListener('DOMContentLoaded', async () => {
    const historyList = document.getElementById('history-list');

    try {
        const response = await fetch('http://localhost:8000/history?agent=GoogleExplainer');
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            historyList.innerHTML = ''; // Clear loading message
            data.history.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';

                const query = document.createElement('div');
                query.className = 'query';
                query.textContent = `"${item.input_text}"`;

                const timestamp = document.createElement('div');
                timestamp.className = 'timestamp';
                timestamp.textContent = new Date(item.timestamp).toLocaleString();

                div.appendChild(query);
                div.appendChild(timestamp);
                historyList.appendChild(div);
            });
        } else {
            historyList.innerHTML = '<p>No recent history.</p>';
        }
    } catch (error) {
        historyList.innerHTML = '<p class="error">Failed to load history. Is server running?</p>';
    }
});
