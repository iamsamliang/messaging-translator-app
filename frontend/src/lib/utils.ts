import { isToday, isYesterday, getDay, format, subDays, startOfDay, isBefore } from "date-fns";

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] as const;

function isBeforeOrOnSevenDaysAgo(sentAt: string) {
    const sixDaysAgo = subDays(new Date(), 6);
    return isBefore(sentAt, startOfDay(sixDaysAgo));
}

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
    if (!isBeforeOrOnSevenDaysAgo(sentAt)) {
        return [DAYS[getDay(sentAt)], formatTime(sentAt)];
    }
    
    const formattedDate = format(sentAt, 'MMMM d, yyyy');
    return [formattedDate, `at ${formatTime(sentAt)}`];
}

export function getMsgPreviewTimeValue(sentAt: string): string {
    if (isToday(sentAt)) return formatTime(sentAt);
    if (isYesterday(sentAt)) return `Yesterday`;
    if (!isBeforeOrOnSevenDaysAgo(sentAt)) {
        return DAYS[getDay(sentAt)];
    }
    
    const formattedDate = format(sentAt, 'P');
    return formattedDate;
}