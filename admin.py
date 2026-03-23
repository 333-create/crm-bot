from flask import Flask, render_template_string, request, redirect, session
import psycopg2, os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey")

LOGIN = os.getenv("ADMIN_LOGIN")
PASSWORD = os.getenv("ADMIN_PASSWORD")

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

HTML = """
<h1>CRM</h1>

<h2>Клієнти</h2>
<ul>
{% for c in clients %}
<li>{{c[1]}} | {{c[2]}} | {{c[3]}} | {{c[4]}}</li>
{% endfor %}
</ul>

<h2>Часи</h2>
<ul>
{% for t in times %}
<li>{{t[1]}}</li>
{% endfor %}
</ul>

<form method="post" action="/add_time">
<input name="time">
<button>Додати</button>
</form>
"""

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["login"] == LOGIN and request.form["password"] == PASSWORD:
            session["auth"] = True
            return redirect("/")
    return '<form method="post"><input name="login"><input name="password"><button>OK</button></form>'

@app.route("/")
def index():
    if not session.get("auth"):
        return redirect("/login")

    cur = conn.cursor()
    cur.execute("SELECT * FROM clients")
    clients = cur.fetchall()

    cur.execute("SELECT * FROM times")
    times = cur.fetchall()

    return render_template_string(HTML, clients=clients, times=times)

@app.route("/add_time", methods=["POST"])
def add_time():
    t = request.form["time"]

    cur = conn.cursor()
    cur.execute("INSERT INTO times (value) VALUES (%s)", (t,))

    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
