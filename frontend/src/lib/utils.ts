export function getCurrentTime(): string {
    const now = new Date();
    return now.toLocaleTimeString('default', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

export function formatTime(sentAt: string): string {
    const date = new Date(sentAt);

    // Format the date to extract only the hour and minute part
    return date.toLocaleTimeString('default', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false // set to true for AM/PM format
    });
}