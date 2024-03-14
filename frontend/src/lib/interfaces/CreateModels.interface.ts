export interface ConversationCreate {
    conversation_name: string | null;
    user_ids: string[];
    is_group_chat: boolean;
}

export interface UserCreate {
    first_name: string;
    last_name: string;
    email: string;
    target_language: string;
    password: string;
    api_key: string;
}

// also same as MessageResponse
export interface MessageCreate {
        conversation_id: number;
        sender_id: number;
        original_text: string;
        orig_language: string;
        sent_at: string;
        sender_name: string | null;
        display_photo: boolean;
        separator?: string[] | null;
}

export interface S3PreSignedURLPOSTRequest {
    filename: string;
    convo_id: number | null;
    about: string;
}