#!/usr/bin/env python3
"""Quick test to debug RSS feeds"""
import httpx
import feedparser

print("=== CoinDesk RSS ===")
r = httpx.get('https://www.coindesk.com/feed')
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("content-type")}')
print(f'First 1000 chars:')
print(r.text[:1000])
print()

feed = feedparser.parse(r.text)
print(f'Entries: {len(feed.entries)}')
print(f'Bozo: {feed.bozo}')
print(f'Feed version: {feed.version}')

print()
print("=" * 60)
print()

print("=== Google News RSS (Bloomberg) ===")
r2 = httpx.get('https://news.google.com/rss/search?q=cryptocurrency+OR+bitcoin+site:bloomberg.com&hl=en-US&gl=US&ceid=US:en')
print(f'Status: {r2.status_code}')
print(f'Content-Type: {r2.headers.get("content-type")}')

feed2 = feedparser.parse(r2.text)
print(f'Entries: {len(feed2.entries)}')
print(f'Bozo: {feed2.bozo}')

if feed2.entries:
    for i, entry in enumerate(feed2.entries[:3]):
        print(f'\n--- Entry {i+1} ---')
        print(f'Title: {entry.title}')
        print(f'Link: {entry.link}')
else:
    print(f'First 1000 chars:')
    print(r2.text[:1000])
