from flask import send_from_directory, render_template, Blueprint


main = Blueprint("main", __name__)

#Home Page
@main.route("/")
def home():
    return render_template("index.html")

#Drug Selection
@main.route("/drug_selection")
def drug_selection():
    return render_template("Drug_selection.html")

#Registration
@main.route("/register", methods=['GET', 'POST'])
def register():
    return render_template("register.html")

#Login
@main.route("/login", methods=['GET', 'POST'])
def login():
    return render_template("login.html")

