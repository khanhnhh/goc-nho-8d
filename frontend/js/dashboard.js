/**
 * Dashboard logic — tải và hiển thị thống kê tuần.
 */

const API_URL = '/api/stats';

document.addEventListener('DOMContentLoaded', loadStats);

async function loadStats() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        
        document.getElementById('activeSessions').textContent = data.active_sessions;
        document.getElementById('messageCount').textContent = data.message_count;
        document.getElementById('blockedCount').textContent = data.blocked_count;
        document.getElementById('period').textContent = data.period;
        
    } catch (error) {
        console.error('Lỗi tải thống kê:', error);
        document.getElementById('activeSessions').textContent = '—';
        document.getElementById('messageCount').textContent = '—';
        document.getElementById('blockedCount').textContent = '—';
        document.getElementById('period').textContent = 'Lỗi';
    }
}

// Tự động tải lại mỗi 5 phút
setInterval(loadStats, 5 * 60 * 1000);
