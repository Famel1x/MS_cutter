from flask import  Flask, render_template, request, redirect, url_for, flash, session 

app = Flask(__name__)
app.secret_key = "1"

# Главная страница
@app.route("/")
def home():
    return render_template("home.html")

# Страница логина
@app.route("/login", methods=["GET", "POST"])
def  login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        #
        #
        #
        if  username == "admin" and password == "admin": 
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Неправильный логин или пароль")
            return redirect(url_for('login'))
    return render_template("login.html")

# Страница регистрации 
@app.route('/register', methods=["GET", "POST"])
def register():
    if  request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        #
        #
        #
        flash("Регистрация прошла успешно")
        return redirect(url_for('login'))
    return render_template("register.html")

# Основной интерфейс 
@app.route("/dashboard")
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html',  username=session['username'])
    else:
        flash("Пожайлуйуйуй")
        return redirect(url_for('login'))
    
#П Профиль пользователя
@app.route("/profile")
def profile():
    if 'username' in session:
        return render_template('profile.html', username=session['username'])
    else:
        flash("Пожайлуйуй")
        return redirect(url_for('login'))

# Выход
@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("ВЫход")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)





