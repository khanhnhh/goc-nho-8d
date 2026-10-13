/**
 * Chat logic — xử lý gửi/nhận tin nhắn, lưu session ID.
 */

const API_URL = '/api/chat';
let sessionId = localStorage.getItem('sessionId') || null;

// DOM elements
const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    addBotMessage('Chào bạn! Mình là Góc nhỏ 8D. Bạn hôm nay thế nào? Kể cho mình nghe đi, mình đang lắng nghe đây. 😊');
});

// Gửi tin nhắn
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    
    // Hiển thị tin nhắn user
    addUserMessage(text);
    messageInput.value = '';
    
    // Hiển thị typing indicator
    showTyping();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: text,
            }),
        });
        
        const data = await response.json();
        
        // Lưu session ID
        sessionId = data.session_id;
        localStorage.setItem('sessionId', sessionId);
        
        // Ẩn typing, hiển thị câu trả lời
        hideTyping();
        addBotMessage(data.reply, data.is_crisis);
        
    } catch (error) {
        console.error('Lỗi gửi tin nhắn:', error);
        hideTyping();
        addBotMessage('Xin lỗi, mình đang gặp sự cố. Em thử lại sau nhé.');
    }
}

function addUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.textContent = text;
    messagesDiv.appendChild(div);
    scrollToBottom();
}

function addBotMessage(text, isCrisis = false) {
    const div = document.createElement('div');
    div.className = `message bot${isCrisis ? ' crisis' : ''}`;
    div.textContent = text;
    messagesDiv.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const div = document.createElement('div');
    div.className = 'typing';
    div.id = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    messagesDiv.appendChild(div);
    scrollToBottom();
    sendBtn.disabled = true;
}

function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
    sendBtn.disabled = false;
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function loadHistory() {
    // Placeholder — có thể tích hợp API lấy lịch sử
}

// Mood check-in
document.querySelectorAll('.mood-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const level = btn.dataset.level;
        const emoji = btn.textContent;
        const text = `Hôm nay mình cảm thấy ${emoji}`;
        
        addUserMessage(text);
        showTyping();
        
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                }),
            });
            
            const data = await response.json();
            sessionId = data.session_id;
            localStorage.setItem('sessionId', sessionId);
            
            hideTyping();
            addBotMessage(data.reply, data.is_crisis);
            
        } catch (error) {
            hideTyping();
            addBotMessage('Cảm ơn em đã chia sẻ cảm xúc.');
        }
    });
});
