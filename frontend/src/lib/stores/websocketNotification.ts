import { writable } from "svelte/store";

interface websocketNotification {
    visible: boolean;
    message: string;
}

function createWebsocketNotifStore() {
    const { set, subscribe } = writable<websocketNotification>({
        visible: false,
        message: ''
    });

    function sendNotification(message: string) {
        set({visible: true, message});
    }

    function reset() {
        set({visible: false, message: ''});
    }

    return {
        subscribe,
        reset,
        sendNotification,
    }
}

export const websocketNotifStore = createWebsocketNotifStore();