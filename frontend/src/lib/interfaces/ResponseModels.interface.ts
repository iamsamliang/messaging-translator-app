export interface MessageReceive {
        conversation_id: number;
        sender_id: number;
        original_text: string;
        orig_language: string;
		first_name: string;
		last_name: string;
        sent_at: string;
        translation_id: number;
}