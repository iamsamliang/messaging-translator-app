export function getCurrentTime(): string {
    const now = new Date();
    return now.toLocaleTimeString('default', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}