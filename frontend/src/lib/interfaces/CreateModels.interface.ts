export interface ConversationCreate {
    conversation_name: string;
    user_ids: string[];
}

export interface UserCreate {
    first_name: string;
    last_name: string;
    email: string;
    target_language: string;
    password: string;
}

export interface MessageCreate {
        conversation_id: number;
        conversation_name: string;
        sender_id: number;
        original_text: string;
        orig_language: string;
		first_name: string;
		last_name: string;
        sent_at: string;
}