import { writable } from "svelte/store";
import type { MessageCreate } from "$lib/interfaces/CreateModels.interface";
import clientSettings from "$lib/config/config.client";
import { differenceInHours } from "date-fns";
import type { MessageReceive } from "$lib/interfaces/ResponseModels.interface";
import { tick } from "svelte";

interface MessageStore {
    messages: MessageCreate[],
    offset: number,
    loadedAll: boolean,
}

function createMessageStore() {
    const { subscribe, set, update } = writable<MessageStore>({
        messages: [],
        offset: 0,
        loadedAll: false,
    });

    let loading = false;
    
    async function fetchMsgs(convoID: number, offset: number, limit: number, loadedAll: boolean, token: string, msgContainer?: HTMLElement): Promise<void> {
        if (loading || loadedAll) return;
        loading = true;

        const response = await fetch(`${clientSettings.apiBaseURL}/messages/${convoID}?offset=${offset}&limit=${limit}`, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (!response.ok) {
            loading = false;
            throw new Error(`Error fetching messages`);
        }

        const fetchedMsgs: MessageCreate[] = await response.json();

        let scrollDifference;

        if (msgContainer) {
            // const scrollTop = msgContainer.scrollTop;
            // const clientHeight = msgContainer.clientHeight;
            // const scrollHeight = msgContainer.scrollHeight;
            
            // offsetFromBottom = scrollHeight - (scrollTop + clientHeight);
            // console.log('Offset from bottom:', offsetFromBottom);

            scrollDifference = msgContainer.scrollHeight - msgContainer.scrollTop;
        }

        update(state => {
            return {
                ...state,
                messages: [...fetchedMsgs, ...state.messages],
                loadedAll: fetchedMsgs.length < limit,
                offset: state.offset + fetchedMsgs.length,
            };
        });

        // requestAnimationFrame(() => {
        //     if (msgContainer) {
        //         msgContainer.scrollTop = msgContainer.scrollHeight - scrollDifference;

        //         // const newScrollTop = msgContainer.scrollHeight - msgContainer.clientHeight - offsetFromBottom;
        //         // msgContainer.scrollTop = newScrollTop;
        //     }
        // })

        if (msgContainer) {
            await tick();

            // @ts-expect-error => scrollDifference will never be undefined if msgContainer isn't undefined
            msgContainer.scrollTop = msgContainer.scrollHeight - scrollDifference;
            
            msgContainer.scrollBy({
                top: -1,
                left: 0,
                behavior: "smooth",
            });

            // const newScrollTop = msgContainer.scrollHeight - msgContainer.clientHeight - offsetFromBottom;
            // msgContainer.scrollTop = newScrollTop;
        }

        loading = false;
    }

    function sendNewMessage(formattedMsg: MessageCreate) {
        update(state => {
            const m = state.messages;
            const msgLen = m.length;

            if (
                msgLen > 0 &&
                m[msgLen - 1].sender_id === formattedMsg.sender_id &&
                differenceInHours(formattedMsg.sent_at, m[msgLen - 1].sent_at) < 2
            )
                m[msgLen - 1].display_photo = false;

            return {
                ...state,
                messages: [...m, formattedMsg],
                offset: state.offset + 1,
            };
        });
    }

    function receiveMessage(receivedMessage: MessageReceive) {
        update(state => {
            const m = state.messages;
            const msgLen = m.length;
            let senderNameVal: string | null = receivedMessage.sender_name;

            const arePrevMsgs = msgLen > 0;

            if (arePrevMsgs) {
                const sameSenderAsPrev = m[msgLen - 1].sender_id === receivedMessage.sender_id;
                const within2Hours = differenceInHours(receivedMessage.sent_at, m[msgLen - 1].sent_at) < 2
                
                if (sameSenderAsPrev && within2Hours) {
                    senderNameVal = null;
                    m[msgLen - 1].display_photo = false;
                } else {
                    m[msgLen - 1].display_photo = true;
                }
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
            
            return {
                ...state,
                messages: [...m, formattedMsg],
                offset: state.offset + 1
            }
        });
    }

    function reset() {
        set({
            messages: [],
            offset: 0,
            loadedAll: false,
        });
        loading = false;
    }

    return {
        subscribe,
        reset,
        fetchMsgs,
        sendNewMessage,
        receiveMessage,
    };
}

export const messageStore = createMessageStore();

// export default messageStore;