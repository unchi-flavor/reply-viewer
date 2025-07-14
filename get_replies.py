import requests
import json
from collections import defaultdict

# あなたのBearer Tokenをここに貼ってね（" " の中に！）
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAMsr3AEAAAAAiVLeQ8AmNrXsD%2BvypcRo4OAIQOk%3DRD5IdNblJJb4A7XBYodpqTygNpbAMzvQNvHOLDqTJW5jWnpnHD"

def create_headers():
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

def get_tweet_by_id(tweet_id, cache):
    if tweet_id in cache:
        return cache[tweet_id]

    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {"tweet.fields": "text"}
    response = requests.get(url, headers=create_headers(), params=params)

    # ↓↓↓ この3行を追加してください（デバッグ用）
    print("元ツイ取得中:", tweet_id)
    print("ステータスコード:", response.status_code)
    print("レスポンス内容:", response.text)

    if response.status_code == 200:
        data = response.json().get("data", {})
        cache[tweet_id] = data
        return data
    else:
        cache[tweet_id] = {"text": "(元ツイート取得失敗)", "id": tweet_id}
        return cache[tweet_id]

def search_recent_replies(username, max_pages=5):
    url = "https://api.twitter.com/2/tweets/search/recent"
    query = f"to:{username} -is:retweet"
    headers = create_headers()
    next_token = None
    grouped = defaultdict(lambda: {"original_text": "", "original_id": "", "replies": []})
    original_cache = {}

    for _ in range(max_pages):
        params = {
            "query": query,
            "tweet.fields": "author_id,created_at,referenced_tweets",
            "max_results": 100
        }
        if next_token:
            params["next_token"] = next_token

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print("Error:", response.status_code)
            print(response.text)
            break

        tweets = response.json().get("data", [])
        for tweet in tweets:
            referenced = tweet.get("referenced_tweets", [])
            original_id = next((ref["id"] for ref in referenced if ref["type"] == "replied_to"), None)
            if not original_id:
                continue

            original = get_tweet_by_id(original_id, original_cache)
            group = grouped[original_id]
            group["original_text"] = original.get("text", "(取得できません)")
            group["original_id"] = original_id
            group["replies"].append({
                "reply_text": tweet["text"],
                "reply_time": tweet["created_at"],
                "reply_user": tweet["author_id"],
                "reply_id": tweet["id"]
            })

        next_token = response.json().get("meta", {}).get("next_token")
        if not next_token:
            break  # もう次がなければ終了

    grouped_list = list(grouped.values())
    with open("replies_grouped.json", "w", encoding="utf-8") as f:
        json.dump(grouped_list, f, ensure_ascii=False, indent=2)
    print("✅ replies_grouped.json に保存しました（元ツイートごとにグループ化）")

# 実行テスト
search_recent_replies("UKIUKI_step", max_pages=5)
