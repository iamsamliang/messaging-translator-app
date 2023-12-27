import type { MessageCreate } from "./interfaces/CreateModels.interface";
import type { IConvo } from "./interfaces/iconvo.interface";
import { messages } from "./stores/stores";
import { selectedConvo } from "./stores/stores";
import { formatTime } from "./utils";

// src/lib/websocket.js
let socket: WebSocket;
let currConvo: IConvo | null = null;
const unsubscribe = selectedConvo.subscribe(value => {
    currConvo = value;
});


export function connectWebSocket() {
    if (typeof window !== "undefined") { // Check if running in browser
        try {
            socket = new WebSocket('ws://localhost:8000/ws/comms');

            socket.onerror = (error) => {
                console.error(`WebSocket error: ${error}`);
            };
            socket.onopen = () => console.log("WebSocket is open now.");
            socket.onmessage = (event) => {
                const receivedMessage: MessageCreate = JSON.parse(event.data);
                receivedMessage.sent_at = formatTime(receivedMessage.sent_at);
                if (receivedMessage.conversation_id === currConvo?.id) {
                    messages.update(m => [...m, receivedMessage]);
                }
            };
            socket.onclose = () => {
                unsubscribe();
                console.log("WebSocket closed.");
            }
            // Define other event handlers as needed
        } catch (error) {
            unsubscribe();
            console.error(`there was an error trying to establish websocket connection: ${error}`);
        }
    }
}

export function sendMessageSocket(message: MessageCreate) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    }
}

export function closeWebSocket() {
    unsubscribe();
    if (socket) {
        socket.close();
    }
}
