#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main import create_app

app = create_app()

with app.app_context():
    client = app.test_client()
    resp = client.get('/article/1')
    
    if resp.status_code == 200:
        html = resp.data.decode('utf-8')
        # Check for article-header
        if 'article-header' in html:
            # Find the line with article-header
            for line in html.split('\n'):
                if 'article-header' in line:
                    print("Found article-header line:")
                    print(line)
                    print()
                    break
        
        # Check for errors
        if 'traceback' in html.lower() or 'error' in html.lower():
            print("⚠️ Errors found in HTML")
            # Find error section
            if 'traceback' in html.lower():
                idx = html.lower().find('traceback')
                print(html[max(0, idx-200):idx+500])
        else:
            print("✓ No errors detected in rendered HTML")
    else:
        print(f"✗ Status code: {resp.status_code}")
        print(resp.data.decode('utf-8')[:500])
