import { writable } from "svelte/store";

function createScrollSignal() {
    const { subscribe, set } = writable<boolean>(false);

    function scrollToBottom() {
        set(true);
    }

    function reset() {
        set(false);
    }

    return {
        subscribe,
        scrollToBottom,
        reset,
    };
}

export const msgContainerScrollSignal = createScrollSignal();