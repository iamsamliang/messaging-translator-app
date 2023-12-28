import { writable } from 'svelte/store';
import type { IConvo } from '$lib/interfaces/iconvo.interface';
import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';
import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';

export const messages = writable<MessageCreate[]>([]);

// const defaultConvo: IConvo = {
//   conversation_name: '',
//   id: -1
// };

export const selectedConvo = writable<IConvo | null>(null);

export const currUserID = writable<number>(-1);

export const latestMessages = writable<Record<number, LatestMessageInfo>>({});