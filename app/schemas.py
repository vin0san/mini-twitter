# app/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class UserProfileResponse(BaseModel):
    id: int
    username: str
    tweet_count: int
    follower_count: int
    following_count: int
    class Config:
        orm_mode = True


# Tweet schemas
class TweetBase(BaseModel):
    content: str

class TweetCreate(TweetBase):
    pass

class TweetUpdate(TweetBase):
    pass

class TweetResponse(TweetBase):
    id: int
    content: str
    owner_id: int
    likes_count: int | None = 0
    created_at: datetime

    class Config:
        orm_mode = True

# Like schemas
class LikeBase(BaseModel):
    tweet_id: int

class LikeResponse(LikeBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

# Follow schemas
class FollowBase(BaseModel):
    followed_id: int

class FollowResponse(BaseModel):
    id: int
    follower_id: int
    followed_id: int

    class Config:
        orm_mode = True