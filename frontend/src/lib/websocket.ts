import type { MessageCreate } from "./interfaces/CreateModels.interface";
import type { LatestMessageInfo } from "./interfaces/UnreadConvo.interface";
import type { IConvo } from "./interfaces/iconvo.interface";
import { messages, latestMessages, selectedConvo, currUserID } from "./stores/stores";
import { formatTime } from "./utils";

// src/lib/websocket.js
let socket: WebSocket;
let currConvo: IConvo | null = null;
let userID: number = -1;

const userid_unsubscribe = currUserID.subscribe(value => {
    userID = value;
});
const selConvo_unsubscribe = selectedConvo.subscribe(value => {
    currConvo = value;
});

function unsubscribe_all(): void {
    selConvo_unsubscribe();
    userid_unsubscribe();
}

export function connectWebSocket() {
    if (typeof window !== "undefined") { // Check if running in browser
        try {
            socket = new WebSocket('ws://localhost:8000/ws/comms');

            socket.onerror = (error) => {
                console.error(`WebSocket error: ${error}`);
            }
            socket.onopen = () => console.log("WebSocket is open now.");
            socket.onmessage = (event) => {
                const receivedMessage: MessageCreate = JSON.parse(event.data);
                if (receivedMessage.conversation_id === currConvo?.id && receivedMessage.sender_id !== userID) {
                    receivedMessage.sent_at = formatTime(receivedMessage.sent_at);
                    const newMessageInfo: LatestMessageInfo = {
                        text: receivedMessage.original_text,
                        time: receivedMessage.sent_at // Format this time as needed
                    };

                    // update messages UI for real-time
                    messages.update(m => [...m, receivedMessage]);
                    // update the conversation block UI for this conversation with latest message for real-time
                    latestMessages.update(messages => {
                        messages[receivedMessage.conversation_id] = newMessageInfo;
                        return messages;
                    });
                }
            }
            socket.onclose = () => {
                unsubscribe_all();
                console.log("WebSocket closed.");
            }
            // Define other event handlers as needed
        } catch (error) {
            unsubscribe_all();
            console.error(`there was an error trying to establish websocket connection: ${error}`);
        }
    }
}

export function sendMessageSocket(message: MessageCreate): void {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    }
}

export function closeWebSocket(): void {
    unsubscribe_all();
    if (socket) {
        socket.close();
    }
}
