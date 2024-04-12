import type { MessageCreate } from "./interfaces/CreateModels.interface";
import type { Conversation, MessageReceive, UpdateConvoName, UpdateConvoPhoto, UpdateConvoSelf, WebsocketPacket, UpdateConvoAddOthers, UpdateConvoRemoveOthers } from "./interfaces/ResponseModels.interface";
import type { LatestMessageInfo } from "./interfaces/UnreadConvo.interface";
import { latestMessages, selectedConvoID, conversations, displayChatInfo, convoMembers, sortedConvoMemberIDs } from "./stores/stores";
import { messageStore } from "./stores/messages";
import { getMsgPreviewTimeValue } from "./utils";
import clientSettings from "./config/config.client";
import { websocketNotifStore } from "./stores/websocketNotification";
import { msgContainerScrollSignal } from "./stores/msgContainerScrollSignal";

// src/lib/websocket.js
let socket: WebSocket;
let currConvoID: number = -1;
let allConversations: Map<number, Conversation>;

const selConvoUnsubscribe = selectedConvoID.subscribe(value => {
    currConvoID = value;
});
const conversationsUnsubscribe = conversations.subscribe(value => {
    allConversations = value;
});

function unsubscribeAll(): void {
    conversationsUnsubscribe();
    selConvoUnsubscribe();
}

export function connectWebSocket(websocketAuthToken: string, currUserEmail: string, token: string) {
    if (typeof window !== "undefined") { // Check if running in browser
        try {
            socket = new WebSocket(`${clientSettings.websocketBaseUrl}/ws/comms?token=${encodeURIComponent(websocketAuthToken)}&user_email=${encodeURIComponent(currUserEmail)}`);

            socket.onerror = (error) => {
                websocketNotifStore.sendNotification("An error occured with your connection. Please refresh the page.")
            }
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
                            `${clientSettings.apiBaseURL}/conversations/${updateData.convo_id}?get_latest_msg=true`,
                            {
                                method: 'GET',
                                headers: {
                                    'Authorization': `Bearer ${token}`
                                }
                            }
                        );
                        if (!response.ok) throw new Error();

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
                        websocketNotifStore.sendNotification("An error occured with a request. Please refresh the page.")
                        return;
                    }
                } else if (packet.type === "delete_self") {
                    // deleting oneself from group chat
                    const updateData = packet.data as UpdateConvoSelf;

                    if (updateData.convo_id === currConvoID) {
                        displayChatInfo.set(false);
                        selectedConvoID.set(-10);
                        messageStore.reset();
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
                        messageStore.receiveMessage(receivedMessage);
                        msgContainerScrollSignal.scrollToBottom();
                        // messageStore.update(state => {
                        //     const m = state.messages;
                        //     const msgLen = m.length;
                        //     let senderNameVal: string | null = receivedMessage.sender_name;

                        //     const arePrevMsgs = msgLen > 0;

                        //     if (arePrevMsgs) {
                        //         const sameSenderAsPrev = m[msgLen - 1].sender_id === receivedMessage.sender_id;
                        //         const within2Hours = differenceInHours(receivedMessage.sent_at, m[msgLen - 1].sent_at) < 2
                                
                        //         if (sameSenderAsPrev && within2Hours) {
                        //             senderNameVal = null;
                        //             m[msgLen - 1].display_photo = false;
                        //         } else {
                        //             m[msgLen - 1].display_photo = true;
                        //         }
                        //     }

                        //     const formattedMsg: MessageCreate = {
                        //         conversation_id: receivedMessage.conversation_id,
                        //         sender_id: receivedMessage.sender_id,
                        //         original_text: receivedMessage.original_text,
                        //         orig_language: receivedMessage.orig_language,
                        //         sent_at: receivedMessage.sent_at,
                        //         sender_name: senderNameVal,
                        //         display_photo: true,
                        //     }
                            
                        //     return {
                        //         ...state,
                        //         messages: [...m, formattedMsg],
                        //         offset: state.offset + 1
                        //     }
                        // });

                        // notify server of this update
                        const patchData = { is_read: 1 };
                        try {
                            const patchResponse: Response = await fetch(
                                `${clientSettings.apiBaseURL}/translations/${receivedMessage.translation_id}`,
                                {
                                    method: 'PATCH',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'Authorization': `Bearer ${token}`
                                    },
                                    body: JSON.stringify(patchData)
                                }
                            );
                            if (!patchResponse.ok) throw new Error();
                        } catch (error) {
                            websocketNotifStore.sendNotification("An error occured with a request. Please refresh the page.");
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
                                `${clientSettings.apiBaseURL}/conversations/${receivedMessage.conversation_id}?get_latest_msg=false`,
                                {
                                    method: 'GET',
                                    headers: {
                                        'Authorization': `Bearer ${token}`
                                    }
                                }
                            );
                            if (!response.ok) throw new Error();

                            const convo = await response.json();

                            conversations.update((currConversations) => {
                                currConversations.set(receivedMessage.conversation_id, { convoName: convo.conversation_name, isGroupChat: convo.is_group_chat, presignedUrl: convo.presigned_url });

                                return currConversations;
                            });
                        } catch (error) {
                            websocketNotifStore.sendNotification("An error occured with a Conversation request. Please refresh the page.")
                            return;
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
                    websocketNotifStore.sendNotification(packet.data as string);
                    // alert(packet.data);
                }
            }
            socket.onclose = () => {
                unsubscribeAll();
                websocketNotifStore.sendNotification(`Connection to messaging app closed. Reload page to reconnect.`);
            }
        } catch (error) {
            unsubscribeAll();
            websocketNotifStore.sendNotification(`There was an error trying to establish connection to messaging app. Reload page to retry.`);
        }
    }
}

export function sendMessageSocket(message: MessageCreate): void {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    }
}

export function closeWebSocket(): void {
    unsubscribeAll();
    if (socket) {
        socket.close();
    }
}
