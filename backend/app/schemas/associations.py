from pydantic import BaseModel


class MemberAssociations(BaseModel):
    user_id: int
    conversation_id: int
