from flask import send_from_directory, render_template, Blueprint

main = Blueprint("main", __name__)

#Home Page
@main.route("/")
def home():
    return render_template("index.html")
