// ============================================
// KŌHAI AI - Chat Application Script
// ============================================

// --- Configuration ---
const CONFIG = {
    API_URL: 'https://viki-maziest-shenita.ngrok-free.dev/chat',  // FastAPI endpoint
    MAX_MESSAGE_LENGTH: 2000,
    TYPING_DELAY: 50,  // ms between typing animation steps
};

// --- DOM Elements ---
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// --- Chat History (for context) ---
let chatHistory = [];

// --- Initialize ---
document.addEventListener('DOMContentLoaded', () => {
    // Auto-resize textarea
    chatInput.addEventListener('input', autoResizeTextarea);

    // Send message handlers
    sendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Focus input on load
    chatInput.focus();
});

// --- Auto-resize Textarea ---
function autoResizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
}

// --- Handle Send Message ---
async function handleSendMessage() {
    const message = chatInput.value.trim();

    if (!message || message.length === 0) return;
    if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
        alert(`Message too long! Maximum ${CONFIG.MAX_MESSAGE_LENGTH} characters.`);
        return;
    }

    // Disable input while processing
    setInputState(false);

    // Add user message to chat
    addMessage(message, 'user');
    chatHistory.push({ role: 'user', content: message });

    // Clear input
    chatInput.value = '';
    autoResizeTextarea();

    // Show typing indicator
    const typingIndicator = showTypingIndicator();

    try {
        // Send to API
        const response = await sendToAPI(message);

        // Remove typing indicator
        typingIndicator.remove();

        // Add assistant response
        addMessage(response, 'assistant');
        chatHistory.push({ role: 'assistant', content: response });

    } catch (error) {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessage('Maaf, terjadi kesalahan. Silakan coba lagi. (Sorry, an error occurred. Please try again.)', 'assistant', true);
    }

    // Re-enable input
    setInputState(true);
    chatInput.focus();
}

// --- Add Message to Chat ---
function addMessage(content, role, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}${isError ? ' error' : ''}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    // Use image for avatar
    const img = document.createElement('img');
    const basePath = role === 'user' ? '/web/img/user' : '/web/img/icon';
    img.src = `${basePath}.jpg`; // Try JPG first
    img.alt = role;

    // Smart fallback: JPG -> PNG -> Emoji
    img.onerror = function () {
        if (this.src.endsWith('.jpg')) {
            // If JPG fails, try PNG
            this.src = `${basePath}.png`;
        } else {
            // If PNG also fails, fallback to emoji
            this.style.display = 'none';
            avatar.textContent = role === 'user' ? '👤' : '🍰';
        }
    };

    avatar.appendChild(img);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const paragraph = document.createElement('p');
    paragraph.textContent = content;

    contentDiv.appendChild(paragraph);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --- Show Typing Indicator ---
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    const img = document.createElement('img');
    img.src = '/web/img/icon.jpg';
    img.alt = 'assistant';
    img.onerror = function () {
        this.style.display = 'none';
        avatar.textContent = '🍰';
    };
    avatar.appendChild(img);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';

    contentDiv.appendChild(indicator);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// --- Send to API ---
async function sendToAPI(message) {
    const response = await fetch(CONFIG.API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            history: chatHistory.slice(-10)  // Send last 10 messages for context
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.response;
}

// --- Toggle Input State ---
function setInputState(enabled) {
    chatInput.disabled = !enabled;
    sendBtn.disabled = !enabled;

    if (enabled) {
        chatInput.placeholder = 'Ketik pesan Anda... (Type your message...)';
    } else {
        chatInput.placeholder = 'Menunggu respons... (Waiting for response...)';
    }
}

// --- Clear Chat ---
function clearChat() {
    chatMessages.innerHTML = `
        <div class="message assistant">
            <div class="message-avatar">
                <img src="/web/bot.jpg" alt="assistant" onerror="this.style.display='none';this.parentNode.textContent='🍰'">
            </div>
            <div class="message-content">
                <p>Halo! Saya Waguri AI, asisten bilingual Anda. Silakan bertanya dalam Bahasa Indonesia atau English! 🌸</p>
            </div>
        </div>
    `;
    chatHistory = [];
}

// --- Export functions for potential external use ---
window.KohaiChat = {
    clearChat,
    chatHistory: () => chatHistory
};
