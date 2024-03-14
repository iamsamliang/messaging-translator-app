import { differenceInHours } from "date-fns";
import type { MessageCreate } from "./interfaces/CreateModels.interface";
import type { Conversation, MessageReceive, UpdateConvoName, UpdateConvoPhoto, UpdateConvoSelf, WebsocketPacket, UpdateConvoAddOthers, UpdateConvoRemoveOthers } from "./interfaces/ResponseModels.interface";
import type { LatestMessageInfo } from "./interfaces/UnreadConvo.interface";
import { messages, latestMessages, selectedConvoID, conversations, displayChatInfo, convoMembers, sortedConvoMemberIDs } from "./stores/stores";
import { getMsgPreviewTimeValue } from "./utils";

// src/lib/websocket.js
let socket: WebSocket;
let currConvoID: number = -1;
let allConversations: Map<number, Conversation>;

const selConvo_unsubscribe = selectedConvoID.subscribe(value => {
    currConvoID = value;
});
const conversations_unsubscribe = conversations.subscribe(value => {
    allConversations = value;
});

function unsubscribe_all(): void {
    conversations_unsubscribe();
    selConvo_unsubscribe();
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
                // const receivedMessage: MessageReceive = JSON.parse(event.data);

                const packet: WebsocketPacket = JSON.parse(event.data);
                
                if (packet.type === "update_convo_name") {
                    const updatedConvo = packet.data as UpdateConvoName;

                    conversations.update((currConversations) => {
                        const convoId = updatedConvo.convo_id;
                        
                        const prevVal = currConversations.get(convoId);

                        if (prevVal) {
                            currConversations.set(convoId, { ...prevVal, convoName: updatedConvo.new_name});
                        }

                        return currConversations;
                    });
                } else if (packet.type === "update_convo_photo") {
                    const newPhotoData = packet.data as UpdateConvoPhoto;

                    conversations.update((currConversations) => {
                        const prevVal = currConversations.get(newPhotoData.convo_id);

                        if (prevVal) {
                            currConversations.set(newPhotoData.convo_id, { ...prevVal, presignedUrl: newPhotoData.url});
                        }

                        return currConversations;
                    });
                } else if (packet.type === "add_self") {
                    // adding oneself to new group chat
                    const updateData = packet.data as UpdateConvoSelf;

                    try {
                        const response: Response = await fetch(
                            `http://localhost:8000/conversations/${updateData.convo_id}?get_latest_msg=true`,
                            {
                                method: 'GET',
                                credentials: 'include'
                            }
                        );
                        if (!response.ok) {
                            const errorResponse = await response.json();
                            console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
                            throw new Error(`Error code: ${response.status}`);
                        }

                        const convo = await response.json();
                        
                        if (convo.latest_message && convo.latest_message.relevant_translation) {
                            const latestMsgUpdater: LatestMessageInfo = {
                                text: convo.latest_message.relevant_translation,
                                time: getMsgPreviewTimeValue(convo.latest_message.sent_at),
                                isRead: convo.latest_message.is_read,
                                translationID: convo.latest_message.translation_id
                            }

                            latestMessages.update((messages) => {
                                messages[convo.id] = latestMsgUpdater;
                                return messages;
                            });
                        }

                        conversations.update((currConversations) => {
                            currConversations.set(updateData.convo_id, { convoName: convo.conversation_name, isGroupChat: convo.is_group_chat, presignedUrl: convo.presigned_url});

                            return currConversations;
                        });
                    } catch (error) {
                        console.error('Error fetching group chat you were added to:', error);
                    }
                } else if (packet.type === "delete_self") {
                    // deleting oneself from group chat
                    const updateData = packet.data as UpdateConvoSelf;

                    if (updateData.convo_id === currConvoID) {
                        displayChatInfo.set(false);
                        selectedConvoID.set(-10);
                        messages.set([]);
                    }

                    conversations.update((currConversations) => {
                        if (currConversations.has(updateData.convo_id)) {
                            currConversations.delete(updateData.convo_id);
                        }

                        return currConversations;
                    });
                } else if (packet.type === "add_members") {
                    // adding other new users to group chat if it's selected

                    const updateData = packet.data as UpdateConvoAddOthers;
                    
                    if (currConvoID === updateData.convo_id) {
                        sortedConvoMemberIDs.set(updateData.members.sorted_member_ids);

                        convoMembers.update((currMembers) => {
                            const newMembers = updateData.members.members;
                            for (const id in newMembers) {
                                const userID = Number(id);
                                currMembers[userID] = newMembers[userID];
                            }

                            return currMembers;
                        });
                    }
                } else if (packet.type === "delete_members") {
                    // delete removed (other) users from group chat if it's selected

                    const updateData = packet.data as UpdateConvoRemoveOthers;
                    
                    if (currConvoID === updateData.convo_id) {
                        sortedConvoMemberIDs.set(updateData.sorted_curr_ids);
                        
                        convoMembers.update((currMembers) => {
                            for (const id in updateData.member_ids) {
                                delete currMembers[Number(id)];
                            }
                            return currMembers;
                        });
                    }
                } else if (packet.type === "message") {
                    const receivedMessage = packet.data as MessageReceive
                    // receivedMessage.sent_at = formatTime(receivedMessage.sent_at);
                    const newMessageInfo: LatestMessageInfo = {
                        text: receivedMessage.original_text,
                        time: getMsgPreviewTimeValue(receivedMessage.sent_at), // Format this time as needed
                        isRead: 1,
                        translationID: receivedMessage.translation_id,
                    };

                    if (receivedMessage.conversation_id === currConvoID) {
                        // if sender_id presigned url expired, update it
                        if (receivedMessage.new_presigned) {
                            convoMembers.update(currConvoMembers => {
                                const targetMember = currConvoMembers[receivedMessage.sender_id]
                                
                                if (targetMember) currConvoMembers[receivedMessage.sender_id] = {...targetMember, presigned_url: receivedMessage.new_presigned }

                                return currConvoMembers;
                            });
                        }
                        // update messages UI for real-time
                        messages.update(m => {
                            const msgLen = m.length;
                            let senderNameVal: string | null = receivedMessage.sender_name;

                            const arePrevMsgs = msgLen > 0;
                            const sameSenderAsPrev = m[msgLen - 1].sender_id === receivedMessage.sender_id;
                            const within2Hours = differenceInHours(receivedMessage.sent_at, m[msgLen - 1].sent_at) < 2

                            if (arePrevMsgs && sameSenderAsPrev && within2Hours) {
                                senderNameVal = null;
                                m[msgLen - 1].display_photo = false;
                            } else if (arePrevMsgs && (!sameSenderAsPrev || !within2Hours)) {
                                m[msgLen - 1].display_photo = true;
                            }

                            const formattedMsg: MessageCreate = {
                                conversation_id: receivedMessage.conversation_id,
                                sender_id: receivedMessage.sender_id,
                                original_text: receivedMessage.original_text,
                                orig_language: receivedMessage.orig_language,
                                sent_at: receivedMessage.sent_at,
                                sender_name: senderNameVal,
                                display_photo: true,
                            }
                            
                            m = [...m, formattedMsg];

                            return m;
                        });

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
                    } else {
                        newMessageInfo["isRead"] = 0;
                    }
                    // update the conversation block UI for this conversation with latest message for real-time
                    latestMessages.update(messages => {
                        messages[receivedMessage.conversation_id] = newMessageInfo;
                        return messages;
                    });

                    // When we receive a message, the conversation must be put at the top of the list
                    
                    // This conversation is a new conversation that we don't have
                    if (!allConversations.has(receivedMessage.conversation_id)) {
                        try {
                            const response: Response = await fetch(
                                `http://localhost:8000/conversations/${receivedMessage.conversation_id}?get_latest_msg=false`,
                                {
                                    method: 'GET',
                                    credentials: 'include'
                                }
                            );
                            if (!response.ok) {
                                const errorResponse = await response.json();
                                console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
                                throw new Error(`Error code: ${response.status}`);
                            }

                            const convo = await response.json();

                            conversations.update((currConversations) => {
                                currConversations.set(receivedMessage.conversation_id, { convoName: convo.conversation_name, isGroupChat: convo.is_group_chat, presignedUrl: convo.presigned_url });

                                return currConversations;
                            });
                        } catch (error) {
                            console.error('Error fetching conversation:', error);
                        }
                    } else {
                        conversations.update((currConversations) => {

                            // Retrieve the current conversation object
                            const oldConvo = currConversations.get(receivedMessage.conversation_id) as Conversation;

                            // needed so the conversation is put at the top
                            currConversations.delete(receivedMessage.conversation_id);

                            currConversations.set(receivedMessage.conversation_id, oldConvo);

                            return currConversations;
                        });
                    }
                } else if (packet.type === "error") {
                    alert(packet.data);
                }
            }
            socket.onclose = () => {
                unsubscribe_all();
                alert("Connection to messaging app closed. Reload page to reconnect.");
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
