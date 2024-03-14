import { isToday, isYesterday, isThisWeek, getDay, format } from "date-fns";

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

export function getCurrentTime(): string {
    return new Date().toISOString();
    // return now.toLocaleTimeString('default', {
    //     hour: '2-digit',
    //     minute: '2-digit',
    //     hour12: false
    // });
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

export function getDateSeparator(sentAt: string): string[] {
    if (isToday(sentAt)) return [`Today`, formatTime(sentAt)];
    if (isYesterday(sentAt)) return [`Yesterday`, formatTime(sentAt)];
    if (isThisWeek(sentAt)) {
        return [DAYS[getDay(sentAt)], formatTime(sentAt)];
    }
    
    const formattedDate = format(sentAt, 'MMMM d, yyyy');
    return [formattedDate, `at ${formatTime(sentAt)}`];
}

export function getMsgPreviewTimeValue(sentAt: string): string {
    if (isToday(sentAt)) return formatTime(sentAt);
    if (isYesterday(sentAt)) return `Yesterday`;
    if (isThisWeek(sentAt)) {
        return DAYS[getDay(sentAt)];
    }
    
    const formattedDate = format(sentAt, 'P');
    return formattedDate;
}