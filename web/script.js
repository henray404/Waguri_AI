// ============================================
// KŌHAI AI - Chat Application Script
// ============================================

// --- Configuration ---
const CONFIG = {
    API_URL: 'http://localhost:8000/chat',  // Ganti ke relative path kalau satu server, atau full URL ngrok
    MAX_MESSAGE_LENGTH: 2000,
};

// --- DOM Elements ---
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const langBtns = document.querySelectorAll('.lang-btn'); // NEW

// --- State ---
let chatHistory = [];
let currentLang = 'id'; // Default language

// --- Initialize ---
document.addEventListener('DOMContentLoaded', () => {
    chatInput.addEventListener('input', autoResizeTextarea);
    sendBtn.addEventListener('click', handleSendMessage);
    
    // Enter key handler
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Language Switch Handler (NEW)
    langBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            langBtns.forEach(b => b.classList.remove('active'));
            // Add active to clicked
            btn.classList.add('active');
            // Update state
            currentLang = btn.getAttribute('data-lang');
            // Update placeholder text
            updatePlaceholder();
            // Optional: Clear chat or notify user
            console.log(`Language switched to: ${currentLang}`);
        });
    });

    chatInput.focus();
});

function updatePlaceholder() {
    if (currentLang === 'id') {
        chatInput.placeholder = 'Ketik pesan Anda...';
    } else {
        chatInput.placeholder = 'Type your message...';
    }
}

function autoResizeTextarea() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
}

async function handleSendMessage() {
    const message = chatInput.value.trim();

    if (!message) return;
    if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
        alert('Message too long!');
        return;
    }

    setInputState(false);
    
    // Add User Message
    addMessage(message, 'user');
    chatHistory.push({ role: 'user', content: message });
    
    chatInput.value = '';
    autoResizeTextarea();

    const typingIndicator = showTypingIndicator();

    try {
        // Send to API with Language param
        const response = await sendToAPI(message, currentLang); // Pass lang here

        typingIndicator.remove();
        
        // Add Assistant Response
        addMessage(response, 'assistant');
        chatHistory.push({ role: 'assistant', content: response });

    } catch (error) {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessage('Maaf, ada error koneksi.', 'assistant', true);
    }

    setInputState(true);
    chatInput.focus();
}

function addMessage(content, role, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}${isError ? ' error' : ''}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    const img = document.createElement('img');
    const basePath = role === 'user' ? 'web/img/user' : 'web/img/icon'; // Sesuaikan path
    img.src = `${basePath}.jpg`;
    img.onerror = function() {
        // Fallback logic
        this.style.display = 'none';
        avatar.textContent = role === 'user' ? '👤' : '🍰';
    };
    avatar.appendChild(img);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const p = document.createElement('p');
    p.textContent = content;
    contentDiv.appendChild(p);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    // (Sama seperti kodemu sebelumnya)
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-avatar">🍰</div>
        <div class="message-content">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

async function sendToAPI(message, lang) {
    const response = await fetch(CONFIG.API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            history: chatHistory.slice(-6), // Limit history
            lang: lang // NEW: Kirim bahasa ke backend
        })
    });

    if (!response.ok) throw new Error('API Error');
    const data = await response.json();
    return data.response;
}

function setInputState(enabled) {
    chatInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
    if (enabled) updatePlaceholder();
    else chatInput.placeholder = 'Waguri sedang berpikir...';
}