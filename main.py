from flask import Flask, render_template

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

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)