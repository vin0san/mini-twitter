# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Table, func, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # tweets thingy
    tweets = relationship("Tweet", back_populates="owner")
    likes = relationship("Like", back_populates="user")

class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="tweets")
    likes = relationship("Like", back_populates="tweet")

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tweet_id = Column(Integer, ForeignKey("tweets.id"))

    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")


class Follow(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    followed_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (  # Fixed typo
        UniqueConstraint('follower_id', 'followed_id', name='unique_follower_followed'),
    )

    follower = relationship("User", foreign_keys=[follower_id])
    followed = relationship("User", foreign_keys=[followed_id])