from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, Column, Integer, Table, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
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
)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    profile_photo: Mapped[Optional[str]] = mapped_column(String(4096))
    email: Mapped[str] = mapped_column(
        Text, unique=True, index=True
    )  # serves as username, unique
    password_hash: Mapped[str] = mapped_column(Text)
    target_language: Mapped[str] = mapped_column(String(100))
    is_admin: Mapped[bool] = mapped_column(default=False)
    api_key: Mapped[str] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(default=False)

    # store all times in UTC
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # For JWT
    pwd_changed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # w/o back_populates unidirectional relationship. From user, can access messages obj
    # But from a message, can't directly get the user obj
    messages_sent: Mapped[List["Message"]] = relationship()

    conversations: Mapped[List["Conversation"]] = relationship(
        secondary=group_member_association,
        back_populates="members",
    )


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    original_text: Mapped[str] = mapped_column(Text)
    orig_language: Mapped[str] = mapped_column(String(100))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    received_at: Mapped[datetime] = mapped_column(nullable=True)

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
        foreign_keys=[conversation_id],
    )
    translations: Mapped[List["Translation"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_conversation_id_sent_at", conversation_id, sent_at.desc()),
    )


class Translation(Base):
    __tablename__ = "translations"
    id: Mapped[int] = mapped_column(primary_key=True)
    translation: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(100))
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    is_read: Mapped[int]

    message: Mapped[Message] = relationship(back_populates="translations")

    # Define a composite index on message_id and target_user_id
    # order of columns matter and affect performance
    # should match order of columns in .where or .filter_by queries
    __table_args__ = (
        Index("idx_message_id_target_user_id", "message_id", "target_user_id"),
    )


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_name: Mapped[Optional[str]] = mapped_column(String(255))
    conversation_photo: Mapped[Optional[str]] = mapped_column(String(255))
    is_group_chat: Mapped[bool]

    # Column for the latest message
    latest_message_id: Mapped[int] = mapped_column(nullable=True, index=True)

    chat_identifier: Mapped[str] = mapped_column(String(64), index=True)

    # Relationships
    messages: Mapped[List[Message]] = relationship(
        back_populates="conversation",
        foreign_keys="[Message.conversation_id]",
        cascade="all, delete-orphan",
    )
    members: Mapped[List[User]] = relationship(
        secondary=group_member_association, back_populates="conversations"
    )
