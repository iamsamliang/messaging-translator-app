import type { IMessage } from "./interfaces/imessage.interface";

// src/lib/websocket.js
let socket: WebSocket;

export function connectWebSocket() {
    if (typeof window !== "undefined") { // Check if running in browser
        socket = new WebSocket('ws://your-backend-websocket-url');

        socket.onopen = () => console.log("WebSocket is open now.");
        socket.onmessage = (event: Event) => {
            // Handle incoming messages
        };
        // Define other event handlers as needed
    }
}

export function sendMessageSocket(message: IMessage) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    }
}

export function closeWebSocket() {
    if (socket) {
        socket.close();
    }
}
