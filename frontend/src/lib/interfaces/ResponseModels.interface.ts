export interface WebsocketPacket {
    type: string;
    data: MessageReceive | UpdateConvoName | UpdateConvoPhoto | UpdateConvoAddOthers | UpdateConvoRemoveOthers | UpdateConvoSelf | string;
}
export interface MessageReceive {
    conversation_id: number;
    sender_id: number;
    original_text: string;
    orig_language: string;
    sender_name: string;
    sent_at: string;
    translation_id: number;
    target_user_id: number;
    new_presigned: string | null;
}

export interface UpdateConvoName {
    convo_id: number;
    new_name: string;
}

export interface UpdateConvoSelf {
    convo_id: number;
}

export interface UpdateConvoAddOthers {
    convo_id: number;
    members: GetMembersResponse;
}

export interface UpdateConvoRemoveOthers {
    convo_id: number;
    member_ids: number[];
    sorted_curr_ids: number[];
}

export interface UpdateConvoPhoto {
    convo_id: number;
    url: string;
}

// Member of a Conversation
export interface Member {
    id: number;
    first_name: string;
    last_name: string;
    profile_photo: string;
    email: string;
    target_language: string;
    is_admin: boolean;
    presigned_url: string | null;
}
export interface Conversation {
    convoName: string;
    isGroupChat: boolean;
    presignedUrl: string | null;
}

export interface GetMembersResponse {
    members: Record<number, Member>;
    sorted_member_ids: number[];
    gc_url: string | null;
}