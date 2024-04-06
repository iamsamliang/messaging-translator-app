import { derived, writable } from 'svelte/store';
import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';
import type { Member, Conversation } from '$lib/interfaces/ResponseModels.interface';

export const conversations = writable<Map<number, Conversation>>(new Map());

export const selectedConvoID = writable<number>(-10);

export const selectedConvo = derived([conversations, selectedConvoID], ([$conversations, $selectedConvoID]) => $conversations.get($selectedConvoID));

export const sortedConvoMemberIDs = writable<number[]>([]);

export const convoMembers = writable<Record<number, Member>>({});

export const currUser = writable<Member>();

export const latestMessages = writable<Record<number, LatestMessageInfo>>({});

export const displayChatInfo = writable<boolean>(false);

export const changeChatName = writable<boolean>(false);

export const isUserSettings = writable<boolean>(false);