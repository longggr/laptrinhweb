from flask import Flask, render_template
from datetime import datetime
import json
import os

def load_articles():
    """Load articles from JSON file"""
    articles_file = os.path.join(os.path.dirname(__file__), 'articles.json')
    try:
        with open(articles_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {articles_file} not found. Using empty articles list.")
        return []

def create_app():
    app = Flask(__name__)
    app.secret_key = "your-secret-key"

    from auth import auth_bp
    from preferences import preferences_bp
    from candidates import candidates_bp
    from search import search_bp
    from majors import majors_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(majors_bp)

    # Load articles from JSON file
    articles = load_articles()

    @app.route("/")
    def home():
        return render_template("home.html", articles=articles)

    def parse_markdown(text):
        """Simple markdown parser for article content"""
        lines = text.split('\n')
        result = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('**') and stripped.endswith(':**'):
                if in_list:
                    result.append('</ul>')
                    in_list = False
                title = stripped[2:-3]
                result.append(f'<h2 class="article-heading">{title}</h2>')
            elif stripped.startswith('- '):
                if not in_list:
                    result.append('<ul class="article-list">')
                    in_list = True
                item = stripped[2:]
                result.append(f'<li>{item}</li>')
            elif stripped == '':
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append('<br>')
            elif stripped:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(f'<p class="article-paragraph">{stripped}</p>')
        
        if in_list:
            result.append('</ul>')
        
        return '\n'.join(result)

    @app.route("/article/<int:article_id>")
    def view_article(article_id):
        article = next((a for a in articles if a["id"] == article_id), None)
        if article:
            article['content_html'] = parse_markdown(article['content'])
            return render_template("article.html", article=article, articles=articles)
        return "Bài viết không tìm thấy", 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)