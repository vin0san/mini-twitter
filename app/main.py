# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy import func

from . import models, schemas, database, auth
from .auth import get_current_user

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.get("/protected")
def read_protected(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello user {current_user['user_id']}, you are authorized!"}

# User Registration
@app.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pass = auth.hash_password(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pass)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# User Login
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/{user_id}", response_model=schemas.UserProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tweet_count = db.query(models.Tweet).filter(models.Tweet.owner_id == user_id).count()
    follower_count = db.query(models.Follow).filter(models.Follow.followed_id == user_id).count()
    following_count = db.query(models.Follow).filter(models.Follow.follower_id == user_id).count()
    return {
        "id": user.id,
        "username": user.username,
        "tweet_count": tweet_count,
        "follower_count": follower_count,
        "following_count": following_count
    }

# --------------------------------Tweets CRUD----------------------

# Create Tweets
@app.post("/tweets", response_model=schemas.TweetResponse)
def create_tweet(
    tweet: schemas.TweetCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    new_tweet = models.Tweet(content=tweet.content, owner_id=current_user["user_id"])
    db.add(new_tweet)
    db.commit()
    db.refresh(new_tweet)
    return new_tweet

# Get all Tweets
@app.get("/tweets", response_model=list[schemas.TweetResponse])
def get_tweets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(database.get_db),
):
    query = db.query(
        models.Tweet.id,
        models.Tweet.content,
        models.Tweet.owner_id,
        models.Tweet.created_at,
        func.count(models.Like.id).label("likes_count")
    ).outerjoin(models.Like).group_by(models.Tweet.id)

    if sort == "asc":
        query = query.order_by(models.Tweet.created_at.asc())
    else:
        query = query.order_by(models.Tweet.created_at.desc())

    tweets = query.offset(skip).limit(limit).all()
    return tweets

# Get my Tweets
@app.get("/tweets/me", response_model=list[schemas.TweetResponse])
def get_mytweets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(
        models.Tweet.id,
        models.Tweet.content,
        models.Tweet.owner_id,
        models.Tweet.created_at,
        func.count(models.Like.id).label("likes_count")
    ).outerjoin(models.Like).filter(
        models.Tweet.owner_id == current_user["user_id"]
    ).group_by(models.Tweet.id)

    if sort == "asc":
        query = query.order_by(models.Tweet.created_at.asc())
    else:
        query = query.order_by(models.Tweet.created_at.desc())

    tweets = query.offset(skip).limit(limit).all()
    return tweets

# Update a Tweet
@app.put("/tweets/{tweet_id}", response_model=schemas.TweetResponse)
def update_tweet(
    tweet_id: int,
    tweet: schemas.TweetUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    db_tweet = db.query(models.Tweet).filter(models.Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    if db_tweet.owner_id != int(current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this tweet")

    db_tweet.content = tweet.content
    db.commit()
    db.refresh(db_tweet)
    return db_tweet

# Delete a Tweet
@app.delete("/tweets/{tweet_id}", status_code=204)
def delete_tweet(
    tweet_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    db_tweet = db.query(models.Tweet).filter(models.Tweet.id == tweet_id).first()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    if db_tweet.owner_id != int(current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this tweet")

    db.delete(db_tweet)
    db.commit()
    return None

# ------------- Likes -----------------
# Like a Tweet
@app.post("/like", response_model=schemas.LikeResponse)
def like_tweet(
    like: schemas.LikeBase,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user),
):
    tweet = db.query(models.Tweet).filter(models.Tweet.id == like.tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    existing_like = db.query(models.Like).filter(
        models.Like.user_id == current_user["user_id"],
        models.Like.tweet_id == like.tweet_id
    ).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="You already liked this tweet")

    new_like = models.Like(user_id=current_user["user_id"], tweet_id=like.tweet_id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like

# Unlike a Tweet
@app.delete("/like/{tweet_id}", status_code=200)
def unlike_tweet(
    tweet_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth.get_current_user),
):
    like = db.query(models.Like).filter(
        models.Like.user_id == current_user["user_id"],
        models.Like.tweet_id == tweet_id
    ).first()

    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(like)
    db.commit()
    return {"message": "Unliked successfully"}

# Who liked a tweet
@app.get("/tweets/{tweet_id}/likes", response_model=list[schemas.UserResponse])
def get_likes(
    tweet_id: int,
    db: Session = Depends(database.get_db),
):
    tweet = db.query(models.Tweet).filter(models.Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    likes = db.query(models.User).join(models.Like).filter(models.Like.tweet_id == tweet_id).all()
    return likes

# Tweet search
@app.get("/tweets/search", response_model=list[schemas.TweetResponse])
def search_tweets(
    keyword: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(database.get_db)
):
    query = db.query(
        models.Tweet.id,
        models.Tweet.content,
        models.Tweet.owner_id,
        models.Tweet.created_at,
        func.count(models.Like.id).label("likes_count")
    ).outerjoin(models.Like).filter(
        models.Tweet.content.ilike(f"%{keyword}%")
    ).group_by(models.Tweet.id).order_by(models.Tweet.created_at.desc())
    tweets = query.offset(skip).limit(limit).all()
    return tweets
# -------------------------------- Follows ----------------------------
# Follow a User
@app.post("/follow", response_model=schemas.FollowResponse)
def follow_user(
    follow: schemas.FollowBase,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    if int(current_user["user_id"]) == follow.followed_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    
    target = db.query(models.User).filter(models.User.id == follow.followed_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User to follow not found")
    
    existing = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user["user_id"],
        models.Follow.followed_id == follow.followed_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You are already following this user")
    
    new_follow = models.Follow(follower_id=current_user["user_id"], followed_id=follow.followed_id)
    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)
    return new_follow

# Unfollow a User
@app.delete("/follow/{user_id}", status_code=200)
def unfollow_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    follow = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user["user_id"],
        models.Follow.followed_id == user_id
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    
    db.delete(follow)
    db.commit()
    return {"message": "Unfollowed successfully"}

# Tweets from followed users
@app.get("/feed", response_model=list[schemas.TweetResponse])
def get_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    following_ids = db.query(models.Follow.followed_id).filter(
        models.Follow.follower_id == current_user["user_id"]
    ).subquery()

    query = db.query(
        models.Tweet.id,
        models.Tweet.content,
        models.Tweet.owner_id,
        models.Tweet.created_at,
        func.count(models.Like.id).label("likes_count")
    ).outerjoin(models.Like).filter(
        models.Tweet.owner_id.in_(following_ids)
    ).group_by(models.Tweet.id)

    if sort == "asc":
        query = query.order_by(models.Tweet.created_at.asc())
    else:
        query = query.order_by(models.Tweet.created_at.desc())

    tweets = query.offset(skip).limit(limit).all()
    return tweets