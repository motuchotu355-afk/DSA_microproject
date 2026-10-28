import re
import random
import time
from flask import Flask, request, jsonify, render_template_string

# ==========================================
# 1. DATA STRUCTURES & ALGORITHMS
# ==========================================

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

class HashNode:
    def __init__(self, key, value=1):
        self.key = key
        self.value = value
        self.next = None

class HashTable:
    def __init__(self, size=100):
        self.size = size
        self.table = [None] * self.size

    def _hash(self, key):
        return sum(ord(c) for c in key) % self.size

    def increment(self, key):
        idx = self._hash(key)
        head = self.table[idx]

        if head is None:
            self.table[idx] = HashNode(key, 1)
            return

        current = head
        while current is not None:
            if current.key == key:
                current.value += 1
                return
            if current.next is None:
                break
            current = current.next

        current.next = HashNode(key, 1)
        
    def decrement(self, key):
        """Removes or decrements a hashtag when a tweet is deleted"""
        idx = self._hash(key)
        current = self.table[idx]
        prev = None
        
        while current is not None:
            if current.key == key:
                current.value -= 1
                if current.value <= 0:  # If count drops to 0, remove the node entirely
                    if prev:
                        prev.next = current.next
                    else:
                        self.table[idx] = current.next
                return
            prev = current
            current = current.next

    def get_all(self):
        items = []
        for head in self.table:
            current = head
            while current is not None:
                items.append([current.key, current.value])
                current = current.next
        return items

def selection_sort(items):
    n = len(items)
    for i in range(n):
        max_idx = i
        for j in range(i + 1, n):
            if items[j][1] > items[max_idx][1]:
                max_idx = j
        items[i], items[max_idx] = items[max_idx], items[i]
    return items

def linear_search_tweets(tweets_list, query):
    matched_tweets = []
    query = query.lower()
    for tweet in tweets_list:
        if query in tweet['content'].lower():
            matched_tweets.append(tweet)
    return matched_tweets

stream_list = LinkedList()
hash_table = HashTable()
tweets_db = []
next_tweet_id = 1


# ==========================================
# 2. FLASK WEB SERVER & FRONTEND UI
# ==========================================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Karunya Tweets</title>
    <style>
        body {
            background-color: #000000;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
        }
        .layout { display: flex; width: 100%; max-width: 1200px; gap: 20px; }
        
        /* LEFT SIDEBAR */
        .sidebar-column { width: 280px; padding: 20px 10px; display: flex; flex-direction: column; gap: 15px; }
        .logo { font-size: 24px; font-weight: bold; padding-left: 15px; margin-bottom: 10px; }
        .nav-btn { background: transparent; color: white; border: none; text-align: left; padding: 15px; font-size: 18px; border-radius: 30px; cursor: pointer; font-weight: bold; transition: background 0.2s; }
        .nav-btn:hover { background-color: #181818; }
        
        .output-box { margin-top: 20px; padding: 15px; border: 1px solid #2f3336; border-radius: 16px; font-family: monospace; font-size: 13px; color: #e7e9ea; white-space: pre-wrap; display: none; background-color: #000000; max-height: 400px; overflow-y: auto; }
        
        /* MIDDLE FEED */
        .feed-column { width: 600px; border-left: 1px solid #2f3336; border-right: 1px solid #2f3336; min-height: 100vh; }
        .header { padding: 15px; font-size: 20px; font-weight: bold; border-bottom: 1px solid #2f3336; backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 10; }
        .post-box { padding: 15px; border-bottom: 1px solid #2f3336; }
        textarea { width: 100%; background-color: transparent; color: white; border: none; font-size: 18px; resize: none; outline: none; }
        .post-controls { display: flex; justify-content: flex-end; margin-top: 10px; }
        .btn-primary { background-color: #ffffff; color: #000000; border: none; border-radius: 20px; padding: 8px 16px; font-weight: bold; cursor: pointer; font-size: 15px; }
        .btn-primary:hover { background-color: #e6e6e6; }
        .feed-container { padding: 15px; }
        
        .tweet { padding: 15px; border: 1px solid #2f3336; border-radius: 16px; margin-bottom: 15px; word-wrap: break-word; background-color: #000000; transition: background 0.2s; }
        .tweet:hover { background-color: #080808; }
        .tweet-header { margin-bottom: 5px; }
        .author-name { font-weight: bold; font-size: 15px; }
        .author-handle { color: #71767b; font-size: 15px; margin-left: 5px; }
        .tweet-content { font-size: 15px; margin-bottom: 10px; line-height: 1.4; }
        .hashtag { color: #1d9bf0; cursor: pointer; }
        .tweet-actions { display: flex; gap: 40px; color: #71767b; font-size: 14px; }
        .action-btn { cursor: pointer; display: flex; align-items: center; gap: 5px; transition: color 0.2s; }
        .action-btn:hover { color: #1d9bf0; }
        .delete-btn:hover { color: #f4212e; }
        
        /* RIGHT SIDEBAR */
        .trends-column { width: 350px; padding-top: 15px; display: flex; flex-direction: column; gap: 20px; }
        .search-box input { width: 100%; background-color: #202327; color: white; border: none; border-radius: 9999px; padding: 14px 20px; font-size: 15px; outline: none; box-sizing: border-box; }
        .search-box input:focus { background-color: #000000; border: 1px solid #1d9bf0; }
        .box { border: 1px solid #2f3336; border-radius: 16px; padding: 15px; }
        .box-title { font-size: 20px; font-weight: bold; margin-bottom: 15px; }
        .trend-item { padding: 10px 0; border-bottom: 1px solid #2f3336; cursor: pointer; transition: background-color 0.2s; }
        .trend-item:hover { background-color: rgba(255,255,255,0.03); }
        .trend-item:last-child { border-bottom: none; padding-bottom: 0; }
        .trend-tag { font-weight: bold; font-size: 15px; margin-bottom: 3px; }
        .trend-count { color: #71767b; font-size: 13px; }
        .freq-table { font-family: monospace; font-size: 13px; color: #1d9bf0; max-height: 200px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="layout">
        <!-- Left Sidebar -->
        <div class="sidebar-column">
            <div class="logo">Karunya Tweets</div>
            <button class="nav-btn" onclick="clearSearchAndHome()">Home</button>
            <button class="nav-btn" onclick="simulateHashtags()">Simulate 50 Tags</button>
            <button class="nav-btn" onclick="printOutput()">Print Output</button>
            
            <!-- In-Page Console Output -->
            <div id="outputDisplay" class="output-box"></div>
        </div>

        <!-- Main Feed -->
        <div class="feed-column">
            <div class="header" id="feedHeader">Home</div>
            <div class="post-box">
                <textarea id="tweetInput" rows="3" placeholder="What is happening? Use #hashtags!"></textarea>
                <div class="post-controls">
                    <button class="btn-primary" onclick="postTweet()">Post</button>
                </div>
            </div>
            <div class="feed-container" id="feed"></div>
        </div>

        <!-- Right Sidebar -->
        <div class="trends-column">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search hashtags (Press Enter)" onkeyup="handleSearch(event)">
            </div>
            <div class="box">
                <div class="box-title">Trends for you</div>
                <div id="trendsList"><div style="color:#71767b; font-size:14px;">No trends yet.</div></div>
            </div>
            <div class="box">
                <div class="box-title">Raw Frequency Table</div>
                <div class="freq-table" id="freqTable">Empty Hash Table</div>
            </div>
        </div>
    </div>

    <script>
        function formatHashtags(text) {
            return text.replace(/(^|\\s)(#[a-zA-Z\\d_]+)/g, '$1<span class="hashtag" onclick="clickTrend(\\'$2\\')">$2</span>');
        }

        async function fetchData(searchQuery = "") {
            let url = '/feed';
            if (searchQuery) {
                url += `?q=${encodeURIComponent(searchQuery)}`;
                document.getElementById('feedHeader').innerText = `Search: ${searchQuery}`;
            } else {
                document.getElementById('feedHeader').innerText = `Home`;
            }

            const feedRes = await fetch(url);
            const tweets = await feedRes.json();
            const feedDiv = document.getElementById('feed');
            feedDiv.innerHTML = '';
            
            if (tweets.length === 0) {
                feedDiv.innerHTML = '<div style="color:#71767b; text-align:center; padding: 20px;">No tweets found.</div>';
            } else {
                tweets.forEach(tweet => {
                    feedDiv.innerHTML += `
                        <div class="tweet">
                            <div class="tweet-header">
                                <span class="author-name">Anonymous</span>
                                <span class="author-handle">@${tweet.author}</span>
                            </div>
                            <div class="tweet-content">${formatHashtags(tweet.content)}</div>
                            <div class="tweet-actions">
                                <div class="action-btn" onclick="likeTweet(${tweet.id})">♡ ${tweet.likes}</div>
                                <div class="action-btn delete-btn" onclick="deleteTweet(${tweet.id})">Delete</div>
                            </div>
                        </div>
                    `;
                });
            }

            const trendsRes = await fetch('/data');
            const data = await trendsRes.json();
            
            const trendsDiv = document.getElementById('trendsList');
            if (data.top_10.length === 0) {
                trendsDiv.innerHTML = '<div style="color:#71767b; font-size:14px;">No trends yet.</div>';
            } else {
                trendsDiv.innerHTML = '';
                data.top_10.forEach((trend, idx) => {
                    trendsDiv.innerHTML += `
                        <div class="trend-item" onclick="clickTrend('${trend[0]}')">
                            <div class="trend-count">${idx + 1} · Trending</div>
                            <div class="trend-tag">${trend[0]}</div>
                            <div class="trend-count">${trend[1]} posts</div>
                        </div>
                    `;
                });
            }

            const freqDiv = document.getElementById('freqTable');
            if (data.all_frequencies.length === 0) {
                freqDiv.innerHTML = "Empty Hash Table";
            } else {
                freqDiv.innerHTML = data.all_frequencies.map(item => `[${item[0]}: ${item[1]}]`).join('<br>');
            }
        }

        function handleSearch(event) {
            if (event.key === 'Enter') {
                const query = document.getElementById('searchInput').value.trim();
                fetchData(query);
            }
        }

        function clickTrend(tag) { document.getElementById('searchInput').value = tag; fetchData(tag); }
        function clearSearchAndHome() { document.getElementById('searchInput').value = ''; fetchData(); window.scrollTo(0,0); }

        async function postTweet() {
            const input = document.getElementById('tweetInput');
            const content = input.value.trim();
            if (!content) return;
            await fetch('/post', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: content }) });
            input.value = '';
            fetchData(document.getElementById('searchInput').value.trim());
        }

        async function likeTweet(id) { 
            await fetch(`/like/${id}`, { method: 'POST' }); 
            fetchData(document.getElementById('searchInput').value.trim()); 
        }

        async function deleteTweet(id) { 
            await fetch(`/delete/${id}`, { method: 'POST' }); 
            fetchData(document.getElementById('searchInput').value.trim()); 
        }

        async function simulateHashtags() { 
            await fetch('/simulate', { method: 'POST' }); 
            fetchData(document.getElementById('searchInput').value.trim()); 
        }

        async function printOutput() { 
            const res = await fetch('/print_output', { method: 'POST' }); 
            const data = await res.json();
            const outDiv = document.getElementById('outputDisplay');
            outDiv.style.display = 'block';
            outDiv.innerText = data.output_text;
        }

        fetchData();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/feed', methods=['GET'])
def get_feed():
    query = request.args.get('q', '').lower()
    if query:
        return jsonify(linear_search_tweets(tweets_db, query))
    return jsonify(tweets_db)

@app.route('/data', methods=['GET'])
def get_data():
    items = hash_table.get_all()
    sorted_items = selection_sort(items)
    return jsonify({"top_10": sorted_items[:10], "all_frequencies": items})

@app.route('/post', methods=['POST'])
def post_tweet():
    global next_tweet_id
    data = request.json
    content = data.get('content', '')
    
    if content:
        author = f"Anon_{random.randint(1000, 9999)}"
        tweets_db.insert(0, {"id": next_tweet_id, "author": author, "content": content, "likes": 0})
        next_tweet_id += 1
        
        hashtags = re.findall(r'#\w+', content)
        for tag in hashtags:
            tag = tag.lower()
            stream_list.append(tag)     
            hash_table.increment(tag)   
            
    return jsonify({"status": "success"})

@app.route('/like/<int:tweet_id>', methods=['POST'])
def like_tweet(tweet_id):
    for t in tweets_db:
        if t['id'] == tweet_id:
            t['likes'] += 1
            break
    return jsonify({"status": "success"})

@app.route('/delete/<int:tweet_id>', methods=['POST'])
def delete_tweet(tweet_id):
    global tweets_db
    # Find the tweet to extract its hashtags before deleting
    tweet_to_delete = next((t for t in tweets_db if t['id'] == tweet_id), None)
    
    if tweet_to_delete:
        hashtags = re.findall(r'#\w+', tweet_to_delete['content'])
        for tag in hashtags:
            # Decrement from Hash Table to keep trends accurate
            hash_table.decrement(tag.lower())
        
        # Remove from database
        tweets_db = [t for t in tweets_db if t['id'] != tweet_id]
        
    return jsonify({"status": "success"})

@app.route('/simulate', methods=['POST'])
def simulate():
    global next_tweet_id
    sample_tags = ["#Karunya", "#BTech", "#Python", "#Hackathon", "#Code", "#Tech", "#Engineering", "#Campus", "#WebDev", "#Linux"]
    
    for _ in range(10):
        tags_for_tweet = random.choices(sample_tags, k=5)
        content = f"Simulated test data chunk: {' '.join(tags_for_tweet)}"
        tweets_db.insert(0, {"id": next_tweet_id, "author": f"AutoBot_{random.randint(100, 999)}", "content": content, "likes": random.randint(0, 50)})
        next_tweet_id += 1
        
        for tag in tags_for_tweet:
            tag = tag.lower()
            stream_list.append(tag)
            hash_table.increment(tag)
            
    return jsonify({"status": "success"})

@app.route('/print_output', methods=['POST'])
def print_output():
    # Build text for the in-page display
    lines = []
    lines.append("="*35)
    lines.append(" EXPECTED PROJECT 08 OUTPUT")
    lines.append("="*35)
    
    lines.append("\n[1] FREQUENCY TABLE:")
    all_items = hash_table.get_all()
    if not all_items:
        lines.append(" -> Table is empty.")
    for tag, count in all_items:
        lines.append(f" {tag.ljust(15)} : {count}")
        
    lines.append("\n[2] TOP 10 TRENDING:")
    sorted_items = selection_sort(all_items)
    for i, (tag, count) in enumerate(sorted_items[:10], 1):
        lines.append(f" #{i} | {tag.ljust(15)} : {count}")
        
    lines.append("\n" + "="*35)
    
    output_text = "\n".join(lines)
    return jsonify({"status": "success", "output_text": output_text})

if __name__ == '__main__':
    print("Starting server... Open http://127.0.0.1:5000 in your browser.")
    app.run(port=5000, debug=False)