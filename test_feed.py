import feedparser

RSS_URL = 'https://rss.marketingtools.apple.com/api/v2/kr/apps/new-apps-we-love/10/apps.rss'
feed = feedparser.parse(RSS_URL)

print(f"Feed Status: {feed.get('status')}")
print(f"Number of entries: {len(feed.entries)}")

if len(feed.entries) > 0:
    entry = feed.entries[0]
    print("Keys in entry:", entry.keys())
    print("-" * 20)
    print("Title:", entry.get('title'))
    print("Link:", entry.get('link'))
    print("Summary:", entry.get('summary'))
    print("Description:", entry.get('description'))
else:
    print("No entries found.")
