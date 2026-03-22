from flask import Flask, render_template_string, request, redirect, session
import json, os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey")

LOGIN = os.getenv("ADMIN_LOGIN")
PASSWORD = os.getenv("ADMIN_PASSWORD")

if not LOGIN or not PASSWORD:
    raise ValueError("ADMIN_LOGIN або ADMIN_PASSWORD не задані (перевір Render → Environment)")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "data.json")

def load_data():
    if not os.path.exists(FILE):
        return {"clients": [], "times": ["10:00", "11:00", "13:00"]}

    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    try:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("❌ Помилка збереження:", e)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>CRM</title>
<style>
body {
    background:#0f172a;
    color:white;
    font-family:Arial;
    padding:20px;
}
.card {
    background:#1e293b;
    padding:20px;
    border-radius:12px;
    margin-bottom:20px;
}
button {
    padding:8px 12px;
    border:none;
    border-radius:6px;
    background:#3b82f6;
    color:white;
    cursor:pointer;
}
input {
    padding:8px;
    border-radius:6px;
    border:none;
    margin-right:10px;
}
table {
    width:100%;
    border-collapse:collapse;
}
td, th {
    padding:10px;
    border-bottom:1px solid #334155;
}
th {
    text-align:left;
}
.stat {
    font-size:18px;
    margin-bottom:10px;
}
</style>
</head>

<body>

<h1>📊 CRM Панель</h1>

<div class="card">
<div class="stat">👥 Клієнтів: {{clients|length}}</div>
<div class="stat">⏰ Вільних слотів: {{times|length}}</div>
</div>

<div class="card">
<h2>🔍 Пошук</h2>
<form method="get">
<input name="q" placeholder="Ім'я або телефон">
<button>Знайти</button>
</form>
</div>

<div class="card">
<h2>👤 Клієнти</h2>
<table>
<tr>
<th>Ім'я</th>
<th>Телефон</th>
<th>Послуга</th>
<th>Час</th>
<th>Дія</th>
</tr>

{% for c in clients %}
<tr>
<td>{{c.name}}</td>
<td>{{c.phone}}</td>
<td>{{c.service}}</td>
<td>{{c.time}}</td>
<td>
<form method="post" action="/delete_client">
<input type="hidden" name="phone" value="{{c.phone}}">
<button style="background:red;">X</button>
</form>
</td>
</tr>
{% endfor %}

</table>
</div>

<div class="card">
<h2>⏰ Часи</h2>

<ul>
{% for t in times %}
<li>{{t}}</li>
{% endfor %}
</ul>

<form method="post" action="/add_time">
<input name="time" placeholder="Новий час">
<button>Додати</button>
</form>

<br>

<form method="post" action="/delete_time">
<input name="time" placeholder="Видалити час">
<button style="background:red;">Видалити</button>
</form>

</div>

</body>
</html>
"""

# 🔐 LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("login") == LOGIN and request.form.get("password") == PASSWORD:
            session["auth"] = True
            return redirect("/")
    return '''
    <form method="post">
        <input name="login" placeholder="логін">
        <input name="password" type="password" placeholder="пароль">
        <button>Увійти</button>
    </form>
    '''

# 🔐 MAIN
@app.route("/")
def index():
    if not session.get("auth"):
        return redirect("/login")

    data = load_data()

    q = request.args.get("q")
    clients = data["clients"]

    if q:
        q = q.lower()
        clients = [c for c in clients if q in c["name"].lower() or q in c["phone"]]

    return render_template_string(HTML, clients=clients, times=data["times"])
# ➕ ADD TIME
@app.route("/add_time", methods=["POST"])
def add_time():
    data = load_data()
    t = request.form["time"]

    if t and t not in data["times"]:
        data["times"].append(t)
        save_data(data)

    return redirect("/")

# ❌ DELETE TIME
@app.route("/delete_time", methods=["POST"])
def delete_time():
    data = load_data()
    t = request.form["time"]

    if t in data["times"]:
        data["times"].remove(t)
        save_data(data)

    return redirect("/")

# ❌ DELETE CLIENT
@app.route("/delete_client", methods=["POST"])
def delete_client():
    data = load_data()
    phone = request.form["phone"]

    data["clients"] = [c for c in data["clients"] if c["phone"] != phone]

    save_data(data)
    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))