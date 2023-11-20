from typing import List, Optional
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    Column,
    Integer,
    Table,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


# Association table for the many-to-many relationship between members and conversations
group_member_association = Table(
    "group_member",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "conversation_id",
        Integer,
        ForeignKey("conversations.id"),
        primary_key=True,
    ),
    Column("joined_datetime", DateTime, default=datetime.utcnow),
    Column("last_read_message_id", Integer, ForeignKey("messages.id"), nullable=True),
)


class User(Base):
    """User Schema with attributes:
    1. id: Primary Key
    2. first_name
    3. last_name
    4. profile_photo: URL or file path
    5. email
    6. password_hash: A hashed version of the user's password.
    7. target_language: The user's language for receiving messages.
    8. created_at: UTC Timestamp when the account was created
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    profile_photo: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(Text, unique=True)  # serves as username
    password_hash: Mapped[str] = mapped_column(Text)
    target_language: Mapped[str] = mapped_column(String(100))
    is_admin: Mapped[bool] = mapped_column(default=False)
    # store all times in UTC
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # w/o back_populates unidirectional relationship. From user, can access messages obj
    # But from a message, can't directly get the user obj
    messages_sent: Mapped[List["Message"]] = relationship()
    messages_received: Mapped[List["Translation"]] = relationship(
        back_populates="user",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        secondary=group_member_association, back_populates="members"
    )


class Message(Base):
    """Message schema with attributes:
    1. id: A unique identifier for the message (Primary Key).
    2. chat_id: Foreign Key linking to the Chats table.
    3. sender_id: Foreign Key linking to the Users table for the sender.
    5. original_text: The original text of the message.
    6. translated_text: The translated text of the message.
    7. orig_language: The language of the original text.
    9. sent_at: Timestamp for when the message was sent.
    10. received_at: Timestamp for when the message was received (optional).
    """

    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id")) # is this needed? We can retrieve all recipients from the conversations table
    original_text: Mapped[str] = mapped_column(Text)
    orig_language: Mapped[str] = mapped_column(String(100))
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )  # index this for faster queries
    received_at: Mapped[datetime] = mapped_column(DateTime)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    translations: Mapped[List["Translation"]] = relationship(back_populates="message")


class Translation(Base):
    __tablename__ = "translations"
    id: Mapped[int] = mapped_column(primary_key=True)
    translation: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(100))
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))

    message: Mapped[Message] = relationship(back_populates="translations")
    user: Mapped[User] = relationship(back_populates="messages_received")


class Conversation(Base):
    """Chat schema with attributes:
    1. id: Primary Key
    2. conversation_name
    """

    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_name: Mapped[str] = mapped_column(String(255))

    # Relationships
    messages: Mapped[List[Message]] = relationship(back_populates="conversation")
    members: Mapped[List[User]] = relationship(
        secondary=group_member_association, back_populates="conversations"
    )
