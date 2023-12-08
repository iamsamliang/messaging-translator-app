import { writable } from 'svelte/store';
import type { IMessage } from '$lib/interfaces/imessage.interface';

export const messages = writable<IMessage[]>([]);
