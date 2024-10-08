from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

from werkzeug.utils import secure_filename

con = sqlite3.connect("users.db", check_same_thread=False)
cur = con.cursor()

UPLOAD_FOLDER = "uploaded"
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

cur.execute("""CREATE TABLE IF NOT EXISTS users(
            username string(80) NOT NULL primary key, 
            email string(120) NOT NULL unique, 
            password string(80) NOT NULL)""")
cur.execute("""CREATE TABLE IF NOT EXISTS videos(
            id integer primary key,
            username integer,
            name string,
            hashtags string,
            full_video_path string not null,
            public_videos string,
            not_public_videos string
            )""")
con.commit()

app = Flask(__name__)
app.secret_key = "1"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главная страница
@app.route("/")
def home():
    datas = cur.execute("""SELECT name, hashtags FROM videos""")
    #print(datas.fetchall())
    name = []
    hashtag = []
    for data in datas.fetchall():
        name.append(data[0])
        hashtag.append(data[1])
    print(name, hashtag)

    return render_template("home.html", name=name, hashtags=hashtag)

@app.route("/archive", methods=["GET", "POST"])
def archive():
    path = app.config['UPLOAD_FOLDER']
    files = os.listdir(path=path)
    full_path = []
    for file in files:
        full_path.append(os.path.join(path, file))
    print(full_path)
    video_files=[]
    for path in full_path:
        video_files.append(path)
    return render_template("archive.html", video_files=full_path)

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == 'POST':
        # Проверка на наличие файла в запросе
        if 'video' not in request.files:
            return redirect(request.url)
        
        file = request.files['video']

        # Проверка на пустое имя файла
        if file.filename == '':
            return redirect(request.url)

        # Проверка на допустимый тип файла
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)  # Безопасное имя файла

            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Путь для сохранения файла
            file.save(file_path)  # Сохранение файла на сервере
            print(file_path)
            video_files = []
            video_files = []
            paths = []
            names = []
            video_names = []
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                if str(filename).endswith(('mp4', 'avi', 'mov','MOV','MP4','AVI')):
                    paths.append(os.path.abspath(f"{app.config['UPLOAD_FOLDER']}/{filename}"))

            full_video_path = cur.execute("""SELECT full_video_path, name FROM videos WHERE public_videos=1""").fetchall()
            full_video_paths = []
            for path in full_video_path:
                names.append(path[1])
                full_video_paths.append(os.path.abspath(path[0]))
            for path in paths:
                p = []
                p.append(path)
                if p[0] in full_video_paths:
                    video_files.append([path, names[paths.index(path)]])
                print(video_files)
            # for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            #     if filename.endswith(('mp4', 'avi', 'mov','MOV','MP4','AVI')):  # Проверка допустимых расширений
            
            #         video_files.append(filename)

            # Передача клипов в шаблон
            return render_template('Shorts_List.html', video_files=video_files, video_names=video_names)

    return render_template('create.html')

# @app.route("/load", methods=["GET", "POST"])
# def load():
#     if request.method == "POST":
#         last_id = cur.execute("SELECT MAX(id) from videos")
#         last_id = last_id.fetchone()[0]
#         if last_id == None:
#             last_id = 0
#         if last_id != None:
#             last_id = int(last_id) + 1
#         username = request.form.get("name")
#         title = request.form.get("title")
#         hashtags = request.form.get("hashtags")
#         video_url = request.form.get("video-url")
#         public = request.form.get("public")
#         if public == "yes":
#             data = [last_id, username, title, hashtags, video_url, "1", "0"]
#         else:
#             data = [last_id, username, title, hashtags, video_url, "0", "1"]
#         cur.execute("""INSERT OR REPLACE INTO videos VALUES(?, ?, ?, ?, ?, ?, ?)""", data)
#         con.commit()
#     return render_template("load.html")

# Страница логина
# @app.route("/login", methods=["GET", "POST"])
# def  login():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")
#         print(username)
#         print(password)
#         check_login = cur.execute(f"""SELECT username, password FROM users where username='{username}'""")
#         data = check_login.fetchone()
#         try:
#             if data[0] == username and data[1] == password:
#                 pass
#         except Exception:
#             pass
#         if  username == "admin" and password == "admin": 
#             session['username'] = username
#             return redirect(url_for('dashboard'))
#         else:
#             flash("Неправильный логин или пароль")
#             return redirect(url_for('login'))
#     return render_template("login.html")

# # Страница регистрации 
# @app.route('/register', methods=["GET", "POST"])
# def register():
#     if  request.method == "POST":
#         username = request.form.get("username")
#         email = request.form.get("email")
#         password = request.form.get("password")
#         data = [username, email, password]
#         try:
#             cur.execute("""INSERT INTO users VALUES(?,?,?)""", data)
#             con.commit()
#             result_of_login = cur.execute(f"""SELECT * FROM users""")
#             print(result_of_login.fetchall())
#             flash("Регистрация прошла успешно")
#             return redirect(url_for('login'))
#         except sqlite3.IntegrityError:
#             flash("Логин или почта уже заняты")
#     return render_template("register.html")

# # Основной интерфейс 
# @app.route("/dashboard")
# def dashboard():
#     if 'username' in session:
#         return render_template('dashboard.html',  username=session['username'])
#     else:
#         flash("Пожайлуйуйуй")
#         return redirect(url_for('login'))

# Профиль пользователя
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

@app.route('/load')
def load_videos():
    # Получаем список всех файлов в папке с видео
    video_files = []
    paths = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if str(filename).endswith(('mp4', 'avi', 'mov')):
            print({app.config['UPLOAD_FOLDER']}/{filename})
            paths.append(os.path.abspath(f"{app.config['UPLOAD_FOLDER']}/{filename}"))
    full_video_path = cur.execute("""SELECT full_video_path FROM videos WHERE public_videos=1""").fetchall()
    full_video_paths = []
    for path in full_video_path:
        full_video_paths.append(os.path.abspath(path[0]))
    for path in paths:
        p = []
        p.append(path)
        if p[0] in full_video_paths:
            video_files.append(path)
    return render_template('load.html', video_files=video_files)

# @app.route('/upload', methods=['GET', 'POST'])
# def upload_video():
#     if request.method == 'POST':
#         # Проверка наличия файла
#         if 'video' not in request.files:
#             return redirect(request.url)
#         file = request.files['video']

#         if file.filename == '':
#             return redirect(request.url)

#         if file:
#             filename = file.filename
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(file_path)

#             print(filename, file_path)
#             last_id = cur.execute("SELECT MAX(id) from videos")
#             last_id = 0 if last_id==None else int(last_id.fetchone()[0])+1
#             public = False
#             if not public:
#                 data = [last_id, "extazy", file_path, "0", "1"]
#             if public:
#                 data = [last_id, "extazy", file_path, "1", "0"]
#             cur.execute("""INSERT OR REPLACE INTO videos VALUES(?, ?, ?, ?, ?)""", data)
#             con.commit()
#             # выбор публичных
#             public_videos = cur.execute("""SELECT * FROM videos
#                                         JOIN users
#                                         ON users.username=videos.username
#                                         WHERE public_videos=1""")
#             print(public_videos.fetchall())

#     return render_template('load.html')

if __name__ == '__main__':
    app.run(debug=True)