import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)

from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# added this line to refresh templates when making changes - to be removed if not needed, pls
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = os.environ.get("SECRET_KEY")

app.jinja_env.add_extension('jinja2.ext.loopcontrols')

mongo = PyMongo(app)


@app.route("/")
def index():
    # for i in animation_info:
    #     mongo.db.animation.insert_one(i)

    return render_template("index.html", index_page=True)


@app.route("/photos")
def photos():
    # for i in animation_info:
    #     mongo.db.animation.insert_one(i)

    return render_template("photos.html")


# ==========handle login logout register======================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for('stories'))
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        else:
            register_user = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            mongo.db.users.insert_one(register_user)
            # put the new user into 'session' cookie
            session["user"] = request.form.get("username").lower()
            flash("Registration Successful!")
            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/story")
def story():
    context = list(mongo.db.stories.find())
    return render_template("story.html", stories=context[::-1])


@app.route("/my_story")
def my_story():
    context = list(mongo.db.stories.find(
        {"created_by": {'$eq': session['user']}}))

    return render_template("my_story.html", stories=context[::-1])


@app.route("/story/add", methods=['POST', ])
def story_add():
    if request.method == 'POST':
        if "user" in session:
            submit = {
                'title': request.form.get('title'),
                'story': request.form.get('story'),
                'created_by': session['user']
            }
            print(submit)
            mongo.db.stories.insert_one(submit)
            return redirect(url_for('story'))
    return redirect(url_for('story'))


@app.route("/story/delete/<story_id>")
def story_delete(story_id):
    if 'user' in session:
        # need more validation if user own this story and allowed to delete it
        mongo.db.stories.delete_one({'_id': ObjectId(story_id)})
        return redirect(url_for('story'))
    return redirect(url_for('story'))


@app.route("/chat")
def chat():
    chat_messages = list(mongo.db.chat.find())
    return render_template("chat.html", chat=chat_messages[::-1])


@app.route("/chat/add", methods=['POST', ])
def chat_add():
    if request.method == 'POST':
        submit = {
            'username': request.form.get('username'),
            'text': request.form.get("text-field")
        }

        mongo.db.chat.insert_one(submit)
        return redirect(url_for('chat'))
    chat_messages = list(mongo.db.chat.find())
    return render_template("chat.html", chat=chat_messages)


@app.route("/chat/delete/<message_id>")
def chat_remove_message(message_id):

    if session['user'] == 'coder' or session['user'] == 'alex':
        mongo.db.chat.delete_one({'_id': ObjectId(message_id)})
    return redirect(url_for('chat'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for('stories'))
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for("index"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))
        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    if "user" in session:
        # remove user from session cookie
        flash("You have been logged out")
        session.pop("user")
        return redirect(url_for("index"))

    return redirect(url_for('index'))


class Error(Exception):  # Class from cloudinary used here temporary
    pass


@app.route("/profile/", methods=["GET", "POST"])
def profile():
    """
    User profile check if user exists, if not redirects to home page
    """
    # grab the session user's username from db
    if request.method == "POST":
        pass
    try:
        mongo.db.users.find_one({
            "username": session["user"]
        })["username"]
    except Error:
        return redirect(url_for("login"))
    if "user" in session:
        blog_list = mongo.db.blog.find(
            {"created_by": {'$eq': session['user']}})
        category_list = list(mongo.db.categories.find())
        return render_template("profile.html", blog_list=blog_list,
                               category_list=category_list)
    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(*args, **kwargs):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
