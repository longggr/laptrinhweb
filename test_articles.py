#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys

try:
    with open('articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    print(f"✓ Successfully loaded {len(articles)} articles from articles.json")
    for article in articles:
        print(f"  - ID {article['id']}: {article['title']}")
        print(f"    Category: {article['category']}")
        print(f"    Content length: {len(article['content'])} characters")
        print()
except Exception as e:
    print(f"✗ Error loading articles: {e}", file=sys.stderr)
    sys.exit(1)
