# tests/test_api.py
import unittest
import requests
from datetime import datetime
from jose import JWTError, jwt

BASE_URL = "http://127.0.0.1:8000"

class TwitterAPITests(unittest.TestCase):  # Fixed class name
    @classmethod
    def setUpClass(cls):
        # Ensure clean state by trying to register users, handle duplicates
        try:
            cls.alice = cls.register_user("alice_test", "password123")
        except AssertionError:
            # User might exist, try logging in
            cls.alice_token = cls.login_user("alice_test", "password123")
            cls.alice = {"id": cls.decode_token(cls.alice_token)["sub"], "username": "alice_test"}
        else:
            cls.alice_token = cls.login_user("alice_test", "password123")

        try:
            cls.bob = cls.register_user("bob_test", "password123")
        except AssertionError:
            cls.bob_token = cls.login_user("bob_test", "password123")
            cls.bob = {"id": cls.decode_token(cls.bob_token)["sub"], "username": "bob_test"}
        else:
            cls.bob_token = cls.login_user("bob_test", "password123")

        # Create tweets for Alice (10) and Bob (5)
        cls.alice_tweets = []
        cls.bob_tweets = []
        for i in range(10):
            tweet = cls.create_tweet(f"Alice's tweet {i+1}", cls.alice_token)
            cls.alice_tweets.append(tweet)
        for i in range(5):
            tweet = cls.create_tweet(f"Bob's tweet {i+1}", cls.bob_token)
            cls.bob_tweets.append(tweet)

        # Alice follows Bob
        cls.follow_user(cls.bob["id"], cls.alice_token)

        # Alice likes Bob's first two tweets
        cls.like_tweet(cls.bob_tweets[0]["id"], cls.alice_token)
        cls.like_tweet(cls.bob_tweets[1]["id"], cls.alice_token)

    @staticmethod
    def register_user(username, password):
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": username, "password": password}
        )
        assert response.status_code == 201, f"Register failed: {response.json()}"
        return response.json()

    @staticmethod
    def login_user(username, password):
        response = requests.post(
            f"{BASE_URL}/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200, f"Login failed: {response.json()}"
        return response.json()["access_token"]
    
    
    @staticmethod
    def decode_token(token):
        
        return jwt.decode(token, "supersecretkey", algorithms=["HS256"])

    @staticmethod
    def create_tweet(content, token):
        response = requests.post(
            f"{BASE_URL}/tweets",
            json={"content": content},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Create tweet failed: {response.json()}"
        return response.json()

    @staticmethod
    def follow_user(followed_id, token):
        response = requests.post(
            f"{BASE_URL}/follow",
            json={"followed_id": followed_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Follow failed: {response.json()}"
        return response.json()

    @staticmethod
    def like_tweet(tweet_id, token):
        response = requests.post(
            f"{BASE_URL}/like",
            json={"tweet_id": tweet_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Like failed: {response.json()}"
        return response.json()

    def test_register_user(self):
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": "charlie_test", "password": "password123"}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "charlie_test")
        self.assertIn("id", data)

        # Test duplicate username
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": "charlie_test", "password": "password123"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Username already registered")

    def test_login(self):
        response = requests.post(
            f"{BASE_URL}/login",
            data={"username": "alice_test", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

        # Test invalid credentials
        response = requests.post(
            f"{BASE_URL}/login",
            data={"username": "alice_test", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid credentials")

    def test_create_tweet(self):
        response = requests.post(
            f"{BASE_URL}/tweets",
            json={"content": "Test tweet"},
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["content"], "Test tweet")
        self.assertEqual(data["owner_id"], int(self.alice["id"]))
        self.assertEqual(data["likes_count"], 0)
        self.assertIn("created_at", data)

    def test_get_tweets_pagination(self):
        response = requests.get(
            f"{BASE_URL}/tweets?skip=0&limit=5&sort=desc"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 5)
        if len(data) > 1:
            self.assertGreaterEqual(
                datetime.fromisoformat(data[0]["created_at"].replace("Z", "+00:00")),
                datetime.fromisoformat(data[1]["created_at"].replace("Z", "+00:00"))
            )

        # Second page
        response = requests.get(
            f"{BASE_URL}/tweets?skip=5&limit=5&sort=desc"
        )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()), 5)

        # Ascending sort
        response = requests.get(
            f"{BASE_URL}/tweets?skip=0&limit=5&sort=asc"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if len(data) > 1:
            self.assertLessEqual(
                datetime.fromisoformat(data[0]["created_at"].replace("Z", "+00:00")),
                datetime.fromisoformat(data[1]["created_at"].replace("Z", "+00:00"))
            )

    def test_get_my_tweets_pagination(self):
        response = requests.get(
            f"{BASE_URL}/tweets/me?skip=0&limit=5&sort=desc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 5)
        for tweet in data:
            self.assertEqual(tweet["owner_id"], int(self.alice["id"]))
        if len(data) > 1:
            self.assertGreaterEqual(
                datetime.fromisoformat(data[0]["created_at"].replace("Z", "+00:00")),
                datetime.fromisoformat(data[1]["created_at"].replace("Z", "+00:00"))
            )

        # Second page
        response = requests.get(
            f"{BASE_URL}/tweets/me?skip=5&limit=5&sort=desc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()), 5)

    def test_update_tweet(self):
        tweet_id = self.alice_tweets[0]["id"]
        response = requests.put(
            f"{BASE_URL}/tweets/{tweet_id}",
            json={"content": "Updated tweet"},
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["content"], "Updated tweet")

        # Test unauthorized update
        response = requests.put(
            f"{BASE_URL}/tweets/{tweet_id}",
            json={"content": "Unauthorized update"},
            headers={"Authorization": f"Bearer {self.bob_token}"}
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_tweet(self):
        tweet_id = self.alice_tweets[1]["id"]
        response = requests.delete(
            f"{BASE_URL}/tweets/{tweet_id}",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 204)

        # Test unauthorized delete
        response = requests.delete(
            f"{BASE_URL}/tweets/{self.alice_tweets[2]['id']}",
            headers={"Authorization": f"Bearer {self.bob_token}"}
        )
        self.assertEqual(response.status_code, 403)

    def test_like_tweet(self):
        tweet_id = self.bob_tweets[2]["id"]
        response = requests.post(
            f"{BASE_URL}/like",
            json={"tweet_id": tweet_id},
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tweet_id"], tweet_id)
        self.assertEqual(data["user_id"], int(self.alice["id"]))

        # Test duplicate like
        response = requests.post(
            f"{BASE_URL}/like",
            json={"tweet_id": tweet_id},
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 400)

    def test_unlike_tweet(self):
        tweet_id = self.bob_tweets[0]["id"]
        response = requests.delete(
            f"{BASE_URL}/like/{tweet_id}",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Unliked successfully")

        # Test unlike non-existent like
        response = requests.delete(
            f"{BASE_URL}/like/{tweet_id}",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 404)

    def test_get_likes(self):
        tweet_id = self.bob_tweets[1]["id"]
        response = requests.get(f"{BASE_URL}/tweets/{tweet_id}/likes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["username"], "alice_test")

    def test_follow_user(self):
        response = requests.post(
            f"{BASE_URL}/follow",
            json={"followed_id": int(self.alice["id"])},
            headers={"Authorization": f"Bearer {self.bob_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["follower_id"], int(self.bob["id"]))
        self.assertEqual(data["followed_id"], int(self.alice["id"]))

        # Test self-follow
        response = requests.post(
            f"{BASE_URL}/follow",
            json={"followed_id": int(self.alice["id"])},
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 400)

    def test_unfollow_user(self):
        # Check if Alice already follows Bob, unfollow if necessary
        response = requests.get(f"{BASE_URL}/feed", headers={"Authorization": f"Bearer {self.alice_token}"})
        if response.status_code == 200 and any(tweet["owner_id"] == int(self.bob["id"]) for tweet in response.json()):
            # Alice already follows Bob, proceed to unfollow
            pass
        else:
            # Follow Bob if not already followed
            self.follow_user(self.bob["id"], self.alice_token)
        response = requests.delete(
            f"{BASE_URL}/follow/{self.bob['id']}",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Unfollowed successfully")

        # Test unfollow non-existent
        response = requests.delete(
            f"{BASE_URL}/follow/{self.bob['id']}",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 404)
    def test_get_feed_pagination(self):
        response = requests.get(
            f"{BASE_URL}/feed?skip=0&limit=3&sort=desc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 3)
        for tweet in data:
            self.assertEqual(tweet["owner_id"], int(self.bob["id"]))
        if len(data) > 1:
            self.assertGreaterEqual(
                datetime.fromisoformat(data[0]["created_at"].replace("Z", "+00:00")),
                datetime.fromisoformat(data[1]["created_at"].replace("Z", "+00:00"))
            )
        if data:
            self.assertIn("likes_count", data[0])
            self.assertIn("created_at", data[0])

        # Second page
        response = requests.get(
            f"{BASE_URL}/feed?skip=3&limit=3&sort=desc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()), 3)

        # Ascending sort
        response = requests.get(
            f"{BASE_URL}/feed?skip=0&limit=3&sort=asc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if len(data) > 1:
            self.assertLessEqual(
                datetime.fromisoformat(data[0]["created_at"].replace("Z", "+00:00")),
                datetime.fromisoformat(data[1]["created_at"].replace("Z", "+00:00"))
            )

    def test_unauthorized_access(self):
        response = requests.get(f"{BASE_URL}/feed")
        self.assertEqual(response.status_code, 401)

    def test_invalid_pagination(self):
        response = requests.get(
            f"{BASE_URL}/feed?skip=-1&limit=3&sort=desc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 422)  # FastAPI validation error

        response = requests.get(
            f"{BASE_URL}/tweets/me?skip=0&limit=101&sort=desc",
            headers={"Authorization": f"Bearer {self.alice_token}"}
        )
        self.assertEqual(response.status_code, 422)
    
    def test_get_user_profile(self):
        response = requests.get(f"{BASE_URL}/users/{self.alice['id']}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "alice_test")
        self.assertEqual(data["tweet_count"], len(self.alice_tweets))
        self.assertEqual(data["follower_count"], 1)  # Bob follows Alice
        self.assertEqual(data["following_count"], 1)  # Alice follows Bob
    
    def test_search_tweets(self):
        response = requests.get(f"{BASE_URL}/tweets/search?keyword=Alice")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 10)
        for tweet in data:
            self.assertIn("Alice", tweet["content"])

if __name__ == "__main__":
    unittest.main()