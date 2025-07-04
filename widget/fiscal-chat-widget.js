// CHAT WIDGET JAVASCRIPT COMPLET
class FiscalChatWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: 'http://localhost:8000',
            municipalityDomain: 'localhost:8000',
            primaryColor: '#007bff',
            welcomeMessage: 'Bună! Cu ce vă pot ajuta?',
            ...config
        };
        
        this.sessionId = this.generateSessionId();
        this.isOpen = false;
        this.isTyping = false;
        
        this.init();
    }
    
    init() {
        this.chatButton = document.getElementById('chatButton');
        this.chatWindow = document.getElementById('chatWindow');
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        this.bindEvents();
        this.applyCustomStyles();
    }
    
    bindEvents() {
        this.chatButton.addEventListener('click', () => this.toggleChat());
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize pentru mobile
        window.addEventListener('resize', () => this.adjustForMobile());
    }
    
    applyCustomStyles() {
        const { primaryColor } = this.config;
        if (primaryColor !== '#007bff') {
            const style = document.createElement('style');
            style.textContent = `
                .chat-button { background: linear-gradient(135deg, ${primaryColor} 0%, ${this.darkenColor(primaryColor)} 100%); }
                .chat-header { background: linear-gradient(135deg, ${primaryColor} 0%, ${this.darkenColor(primaryColor)} 100%); }
                .message.user .message-content { background: ${primaryColor}; }
                .send-button { background: ${primaryColor}; }
                .chat-input input:focus { border-color: ${primaryColor}; }
            `;
            document.head.appendChild(style);
        }
    }
    
    darkenColor(color) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = -20;
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    toggleChat() {
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            this.chatWindow.classList.add('open');
            this.chatButton.classList.add('open');
            this.chatButton.innerHTML = '✕';
            this.messageInput.focus();
        } else {
            this.chatWindow.classList.remove('open');
            this.chatButton.classList.remove('open');
            this.chatButton.innerHTML = '💬';
        }
    }
    
    async sendMessage(messageText = null) {
        const message = messageText || this.messageInput.value.trim();
        if (!message || this.isTyping) return;
        
        // Adaugă mesajul utilizatorului
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        
        // Arată typing indicator
        this.showTyping();
        
        try {
            console.log('Sending message:', message);
            console.log('API URL:', `${this.config.apiUrl}/api/chat`);
            
            const requestBody = {
                content: message,
                municipality_domain: this.config.municipalityDomain || 'localhost:8000',
                session_id: this.sessionId
            };
            
            console.log('Request body:', requestBody);
            
            const response = await fetch(`${this.config.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Response error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            // Simulează timp de gândire pentru UX mai bun
            setTimeout(() => {
                this.hideTyping();
                this.addMessage(data.response || 'Am primit mesajul dvs.', 'bot');
                this.sendButton.disabled = false;
            }, 1000);
            
        } catch (error) {
            console.error('Chat error:', error);
            setTimeout(() => {
                this.hideTyping();
                this.addErrorMessage(`Eroare de conexiune: ${error.message}. Vă rugăm să încercați din nou.`);
                this.sendButton.disabled = false;
            }, 1000);
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll la ultimul mesaj
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    addErrorMessage(content) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = content;
        this.chatMessages.appendChild(errorDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showTyping() {
        this.isTyping = true;
        this.typingIndicator.style.display = 'block';
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    hideTyping() {
        this.isTyping = false;
        this.typingIndicator.style.display = 'none';
    }
    
    adjustForMobile() {
        // Ajustări pentru mobile - implementate în CSS
    }
    
    // API public pentru integrare
    static init(config) {
        return new FiscalChatWidget(config);
    }
}

// Inițializează widget-ul
const widget = FiscalChatWidget.init({
    apiUrl: 'http://localhost:8000',
    municipalityDomain: 'localhost:8000',
    primaryColor: '#007bff',
    welcomeMessage: 'Bună! Cu ce vă pot ajuta privind taxele și impozitele?'
});

// Funcție pentru butoanele de test
function sendTestMessage(message) {
    if (!widget.isOpen) {
        widget.toggleChat();
    }
    setTimeout(() => {
        widget.sendMessage(message);
    }, 300);
}

// Expune la global pentru integrare
window.FiscalChatWidget = FiscalChatWidget;

// Debug helper
window.debugWidget = function() {
    console.log('Widget config:', widget.config);
    console.log('Session ID:', widget.sessionId);
    console.log('Is open:', widget.isOpen);
};