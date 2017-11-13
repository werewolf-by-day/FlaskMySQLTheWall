from flask import Flask, redirect, render_template, session, flash, request
import md5
from mysqlconnection import MySQLConnector

app = Flask(__name__)

app.secret_key = "keepItSecretKeepItSafe"
salt = "popcorn"

mysql = MySQLConnector(app, 'the_wall_flask')

@app.route('/')
def index():
	return render_template('loginreg.html')

@app.route('/users', methods=["POST"])
def register():
	hashed_pw = md5.new(salt+request.form['password']+salt).hexdigest()
	query_reg = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:fn, :ln, :em, :pw, NOW(), NOW())"
	data = {
	"fn": request.form['first_name'],
	"ln": request.form['last_name'],
	"em": request.form['email'],
	"pw": hashed_pw
	}
	mysql.query_db(query_reg, data)
	return redirect('/')

@app.route('/login', methods=["POST"])
def login():
	query_login = "SELECT * FROM users WHERE email = :em"
	data = {"em": request.form['email']}
	found_user = mysql.query_db(query_login, data)
	hashed_input = md5.new(salt+request.form['password']+salt).hexdigest()
	if len(found_user)>0 and hashed_input == found_user[0]['password']:
		session["user_id"] = found_user[0]['id']
		session["user_name"] = found_user[0]['first_name'] + " " + found_user[0]['last_name']
		return redirect('/the_wall')
	else:
		return redirect('/')

@app.route('/messages', methods=["POST"])
def create_message():
	query_message = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES(:u_id, :msg, NOW(), NOW())"
	data = {
	"u_id": session["user_id"],
	"msg": request.form['message']
	}
	mysql.query_db(query_message, data)
	return redirect('/the_wall')

@app.route('/comments/<message_id>', methods=["POST"])
def create_comment(message_id):
	query_comments = "INSERT INTO comments (user_id, message_id, comment, created_at, updated_at) VALUES(:u_id, :m_id, :cmt, NOW(), NOW())"
	data = {
	"u_id": session["user_id"],
	"m_id": message_id,
	"cmt": request.form["comment"]
	}
	mysql.query_db(query_comments, data)
	return redirect('/the_wall')


@app.route('/the_wall')
def wall():
	query = "SELECT users.first_name, users.last_name, DATE_FORMAT(messages.created_at, '%M-%D %Y') as created_at, messages.message, messages.id FROM messages JOIN users ON messages.user_id = users.id"
	all_messages = mysql.query_db(query)
	print all_messages
	for message in all_messages:
		message['comments'] = []
		query = "SELECT users.first_name, users.last_name, DATE_FORMAT(comments.created_at, '%M-%D %Y') as created_at, comments.comment, comments.id FROM comments JOIN users ON comments.user_id = users.id WHERE comments.message_id = :m_id"
		data = {"m_id": message['id']}
		message['comments']=mysql.query_db(query,data)
	return render_template('the_wall.html', messages = all_messages)

app.run(debug = True)
