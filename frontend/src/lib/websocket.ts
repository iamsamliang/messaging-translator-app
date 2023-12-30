import type { MessageCreate } from "./interfaces/CreateModels.interface";
import type { MessageReceive } from "./interfaces/ResponseModels.interface";
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
            socket.onmessage = async (event) => {
                const receivedMessage: MessageReceive = JSON.parse(event.data);
                receivedMessage.sent_at = formatTime(receivedMessage.sent_at);
                const newMessageInfo: LatestMessageInfo = {
                    text: receivedMessage.original_text,
                    time: receivedMessage.sent_at, // Format this time as needed
                    isRead: 1,
                    translationID: receivedMessage.translation_id
                };

                if (receivedMessage.conversation_id === currConvo?.id) {
                    if (receivedMessage.sender_id !== userID) {

                        // update messages UI for real-time
                        messages.update(m => [...m, receivedMessage]);

                        // notify server of this update
                        const patchData = { is_read: 1 };
                        const patchResponse: Response = await fetch(
                            `http://localhost:8000/translations/${receivedMessage.translation_id}`,
                            {
                                method: 'PATCH',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                credentials: 'include',
                                body: JSON.stringify(patchData)
                            }
                        );
                        if (!patchResponse.ok) {
                            const errorResponse = await patchResponse.json();
                            console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
                            throw new Error(`Error code: ${patchResponse.status}`);
                        }
                    }
                } else {
                    newMessageInfo["isRead"] = 0;
                }
                // update the conversation block UI for this conversation with latest message for real-time
                latestMessages.update(messages => {
                    messages[receivedMessage.conversation_id] = newMessageInfo;
                    return messages;
                });
            }
            socket.onclose = (event) => {
                unsubscribe_all();
                const error_msg = JSON.parse(event.code.toString());
                console.log(`Websocket code: ${error_msg}`);
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
