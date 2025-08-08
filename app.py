import bcrypt
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
#db_location = 'var/database.db'

app.secret_key = 'AAA'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(app)

class Users(db.Model):
	__tablename__ = "users_table"
	
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(30))
	password = db.Column(db.String(30))
    
	posts = db.relationship('Posts', backref='author', lazy=True)
	likes = db.relationship('Likes', backref='author', lazy=True)
	
class Posts(db.Model):
	__tablename__ = "posts_table"
	
	post_id = db.Column(db.Integer, primary_key=True)
	author_id = db.Column(db.Integer, db.ForeignKey('users_table.user_id'))
	datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	content = db.Column(db.String(255))
	likes = db.relationship('Likes', backref='post', lazy=True)
	
	def likes_as_flat_user_id_list(self): #Idea from https://stackoverflow.com/questions/46554767/different-text-depending-on-if-user-has-liked-a-post
		returnvalues = []
		for n in self.likes:
			returnvalues.append(n.user_id)
		return returnvalues


    
class Likes(db.Model):
	__tablename__ = "likes_table"
    
	like_id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users_table.user_id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts_table.post_id'))
	
	    
#def init_db():
    

@app.route("/")
def default():
	return redirect(url_for("home"))
        
@app.route("/home")
def home():
	posts = Posts.query.order_by(Posts.datetime.desc()).all()
	return render_template("posts.html", posts=posts)

@app.route("/create", methods=["GET", "POST"])
def create_post():
	if "user_id" not in session:
		return redirect(url_for("login"))

	if request.method == "POST":
		content = request.form.get("content")
		new_post = Posts(author_id=session["user_id"], content=content)
		db.session.add(new_post)
		db.session.commit()
		return redirect(url_for("home"))

	return render_template("create_post.html")

@app.route("/profile/<int:user_id>")
def profile(user_id):
	user = Users.query.get_or_404(user_id)
	posts = Posts.query.filter_by(author_id=user_id).all()
	return render_template("profile.html", user=user, posts=posts)

@app.route("/create_profile", methods=["GET", "POST"])
def create_profile():
	if request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")

		if username and password:
			password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
			new_user = Users(username=username, password=password_hashed)
			db.session.add(new_user)
			db.session.commit()
			return redirect(url_for("home"))

	return render_template("create_profile.html")


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")
        
		user = Users.query.filter_by(username=username).first()
		if user:
			password_data = user.password
			password_hashed = bcrypt.hashpw(password.encode('utf-8'), password_data)
			user = Users.query.filter_by(username=username, password=password_hashed).first()
        
			if user:
				session["user_id"] = user.user_id
				session["user_name"] = user.username
				return redirect(url_for("home"))
			else:
				return "Invalid credentials"
		else:
			return "Invalid credentials"


	return render_template("login.html")

@app.route("/logout")
def logout():
	session.pop("user_id", None)
	session.pop("user_name", None)
	return redirect(url_for("home"))

@app.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
	if "user_id" not in session:
		return redirect(url_for("login"))

	user_id = session["user_id"]
	existing_like = Likes.query.filter_by(user_id=user_id, post_id=post_id).first()

	if existing_like:
		db.session.delete(existing_like)
	else:
		new_like = Likes(user_id=user_id, post_id=post_id)
		db.session.add(new_like)
	db.session.commit()
	return redirect(request.referrer or url_for("home"))


if __name__ == "__main__":
	with app.app_context():
		db.create_all()
	app.run(host='0.0.0.0', port=5000, debug=True)
