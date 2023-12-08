
// Send the message to the server over websockets
function initializeSendMessageForm(): void {
    const form: HTMLFormElement | null = document.getElementById("sendMessageForm") as HTMLFormElement;
    const input: HTMLInputElement | null = document.getElementById("messageInput") as HTMLInputElement;
    const button: HTMLElement | null = document.getElementById("sendButton");

    if (!form || !input || !button) {
        console.error("Form elements not found");
        return;
    }

    button.addEventListener("click", (event: Event): void => {
        // don't reload page
        event.preventDefault();
        const message: string = input.value.trim();
        
        if (validateMessage(message)) {
            const messagesContainer: Element | null = document.querySelector(".message-container");
            if (!messagesContainer) {
                console.error("Container for all messages not found");
                return;
            }

            // new message content
            const newMessageContent: HTMLDivElement = document.createElement("div");
            newMessageContent.classList.add("message-content");
            newMessageContent.textContent = message;

            // new time
            const newMessageTime: HTMLDivElement = document.createElement("div");
            newMessageTime.classList.add("message-time");
            newMessageTime.textContent = getCurrentTime()

            // new message container
            const newMessageDiv: HTMLDivElement = document.createElement("div");
            newMessageDiv.classList.add("message");
            newMessageDiv.appendChild(newMessageContent);
            newMessageDiv.appendChild(newMessageTime);

            // add to messages container
            messagesContainer.appendChild(newMessageDiv);

            // send message to server here
            // send message function //
            input.value = "";
        }
        else {
            alert("Please enter a message!");
        }
    });

    input.addEventListener("keypress", (event: KeyboardEvent): void => {
        if (event.key === "Enter") {
            event.preventDefault();
            button.click();
        }
    });
}

function validateMessage(message: string): boolean {
    // implement more robust validation
    return message.length > 0;
}

function getCurrentTime(): string {
    const now = new Date();
    return now.toLocaleTimeString("default", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });
}

export { initializeSendMessageForm };