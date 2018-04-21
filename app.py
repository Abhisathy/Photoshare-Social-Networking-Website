import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from flask import send_from_directory
# for image uploading
from werkzeug.utils import secure_filename
import os, base64, datetime

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!


# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email FROM Users")
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users")
    return cursor.fetchall()

def getMultipleDetails():
    cursor = conn.cursor()
    #email = cursor.execute("SELECT email from Users")

class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()

    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    #user.is_authenticated = request.form['password'] == pwd
    if request.form['password'] == pwd:
        #user.is_authenticated = True
        return user
    else:
        return

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''if flask.request.method == 'GET':
        return
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(flask.url_for('home'))  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return render_template('main.html', message='Welcome to Photoshare')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')

@app.route("/exists_friends/<name>", methods=['GET', 'POST'])
@flask_login.login_required
def exists_friends(name):

    if request.method == 'GET':
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT f_name FROM Users WHERE f_name = '{0}'"
        if (cursor.execute(query.format(name))):
            naam = cursor.fetchone()[0]
            return render_template('exists_friends.html', name=naam)
        # must get value of yesno here,

        #if yesno= Y, then send name to add_friend(friendemail) below
        else:
            return render_template('exists_friends.html', name='none')
    else:
        yesno = request.form['yesno']
        if yesno == "Y":
            return redirect(url_for('add_friend', friendname=name))
        else:
            return redirect(url_for('search_friends'))

@app.route("/unfriend", methods=['GET', 'POST'])
@flask_login.login_required
def unfriend():
    unfriendemail = request.form['unfriendemail']
    print(unfriendemail)
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT users_id FROM Users WHERE email = '{0}'".format(unfriendemail))
    rows = cursor.fetchall()
    friendid = 0
    for row in rows:
        if row[0] is not None:
            friendid = row[0]
    print(friendid)
    cursor.execute("DELETE FROM Friendship WHERE users_id1 = '{0}' AND users_id2 = '{1}'".format(uid, friendid))
    cursor.execute("DELETE FROM Friendship WHERE users_id1 = '{1}' AND users_id2 = '{0}'".format(uid, friendid))
    conn.commit()
    return redirect(url_for('friendlist'))

@app.route("/add_friend", methods=['GET', 'POST'])
@flask_login.login_required
def add_friend():
#friendemail should be returned from exists_friends(name)
    friendname = request.form['friend']
    print(friendname)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor1 = conn.cursor()
    cursor.execute("SELECT users_id FROM Users WHERE email = '{0}'".format(friendname))
    rows = cursor.fetchall()
    friendid = 0
    for row in rows:
        if row[0] is not None:
            friendid = row[0]
    print(friendid)
    uid = getUserIdFromEmail(flask_login.current_user.id)
    #cursor1.execute("SELECT f_name FROM Users WHERE users_id = '{0}'".format(uid))
    #main_user = cursor1.fetchall()
    #if main_user is not None:
    cursor.execute("INSERT INTO Friendship (users_id1, users_id2) VALUES ('{0}', '{1}')".format(uid, friendid))
    cursor.execute("INSERT INTO Friendship (users_id1, users_id2) VALUES ('{0}', '{1}')".format(friendid, uid))
    conn.commit()
    #########################NEXT 4 LINES JUST TO CHECK IF THEY ARE NOW FRIENDS################
    return redirect(url_for('friendlist'))


@app.route("/search_friends", methods=['GET','POST'])
@flask_login.login_required
def search_friends():
    #friendname = request.form["friendname"]
    if request.method == 'POST':
        username = request.form['fname']
        return redirect(url_for('exists_friends', name=username))
    else:
        return render_template('search_friends.html')
        #username = request.args.get('username')
        #return redirect(url_for('exists_friends', name=username))

# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('signup.html')

'''@app.route("/register_error", methods=['GET'])
def register_error():
    return render_template('user_exists.html')'''

@app.route("/register", methods=['POST'])
def register_user():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        fname = request.form.get('firstname')
        lname = request.form.get('lastname')
        dob = request.form.get('birthday')
        city = request.form.get('hometown')
        gender = request.form.get('gender')
    except:
        print("chk1")
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print("chk2")
        print(cursor.execute("INSERT INTO Users (gender, email, password, dob, city, f_name, l_name) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(gender, email, password, dob, city, fname, lname)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('main.html', message="Welcome to Photoshare", message1='\nAccount Created! \n Please login to continue.')
    else:
        return render_template('signup.html', supress=True)

@app.route("/getPhoto", methods=['POST'])
@flask_login.login_required
def getPhoto():
    photo = request.form['photo']
    like = request.form['like']
    caption = request.form['caption']
    pic_id = request.form['pic_id']
    nlike = request.form['nlike']
    currentU = request.form.get('currentU')
    com = []
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT C.content, C.DOC, U.f_name FROM Comment AS C, Users AS U WHERE picture_id = '{0}' AND C.users_id = U.users_id".format(pic_id))
    temp = cursor.fetchall()
    conn.commit()
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT f_name FROM Users WHERE users_id IN (SELECT users_id FROM Liketable WHERE picture_id = '{0}')".format(pic_id))
    likelist = cursor.fetchall()
    conn.commit()
    for c in temp:
        if c[0] is not None:
            com.append((c[0], c[1], c[2]))
    liked = []
    for l in likelist:
        if l[0] is not None:
            liked.append(l[0])
    if currentU == 'true':
        return render_template('testShowPhoto.html', photo=photo, like=like, liked=liked, caption=caption, pic_id=pic_id, nlike=nlike, comments=com, currentU=currentU)
    else:
        return render_template('testShowPhoto.html', photo=photo, like=like, liked=liked, caption=caption, pic_id=pic_id, nlike=nlike, comments=com)

@app.route("/deletePhoto", methods=['POST'])
@flask_login.login_required
def deletePhoto():
    pic_id = request.form['deleteP']
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM APassoc WHERE picture_id = '{0}'".format(pic_id))
    cursor.execute("DELETE FROM ASSOCIATE WHERE picture_id  ='{0}'".format(pic_id))
    cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pic_id))
    conn.commit()
    return redirect(url_for('profile'))
def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT users_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

@app.route('/addPhoto', methods=['POST'])
@flask_login.login_required
def addPhoto():
    a_name = request.form['addA']
    return render_template('album.html', album=a_name)

@app.route('/deleteAlbum', methods=['POST'])
@flask_login.login_required
def deleteAlbum():
    a_name = request.form['deleteA']
    cursor = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute("SELECT picture_id FROM APassoc WHERE a_id IN (SELECT a_id FROM Album WHERE users_id ='{0}' AND a_name ='{1}')".format(uid, a_name))
    rows =cursor.fetchall()
    cursor.execute("DELETE FROM APassoc WHERE a_id IN (SELECT a_id FROM Album WHERE users_id ='{0}' AND a_name ='{1}')".format(uid, a_name))
    for row in rows:
        if row[0] is not None:
            cursor.execute("DELETE FROM ASSOCIATE WHERE picture_id  ='{0}'".format(row[0]))
            cursor.execute("DELETE FROM Pictures WHERE picture_id  ='{0}'".format(row[0]))
    cursor.execute("DELETE FROM Album WHERE users_id ='{0}' AND a_name ='{1}'".format(uid, a_name))
    conn.commit()
    return redirect(url_for('profile'))

def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True


# end login code

@app.route("/home", methods=['GET','POST'])
@flask_login.login_required
def home():
    abc = popular_tags()
    a = []
    all = []
    for row1 in abc:
        if row1[0] is not None:
            a.append(row1[0])
    uid = getUserIdFromEmail(flask_login.current_user.id)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT f_name FROM Users WHERE users_id = '{0}'".format(uid))
    row = cursor.fetchall()
    conn.commit()
    uname = ""
    for r in row:
        if r[0] is not None:
            uname = r[0]

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT f_name, l_name FROM Users WHERE users_id IN (SELECT users_id FROM Pictures GROUP BY users_id ORDER BY count(picture_id) DESC) AND users_id IN (SELECT users_id FROM Comment WHERE picture_id IN (SELECT picture_id FROM Pictures WHERE users_id <> '{0}') GROUP BY users_id ORDER BY count(picture_id) DESC)".format(uid))
    user_activity = cursor.fetchall()
    conn.commit()
    u = []
    com = []
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, caption, picture_id, users_id FROM Pictures WHERE picture_id IN (SELECT picture_id FROM ASSOCIATE WHERE Hashtag IN (SELECT * FROM (SELECT Hashtag FROM ASSOCIATE WHERE picture_id IN (SELECT picture_id FROM Pictures WHERE users_id = '{0}') GROUP BY Hashtag ORDER BY count(picture_id) DESC LIMIT 5) temp_tab) GROUP BY picture_id ORDER BY count(Hashtag) DESC) AND users_id != '{0}'".format(uid))
    tags = cursor.fetchall()
    print(tags)
    for row in tags:
        if row[0] is not None:
            #print("/static/" + str(row[3]) + "_")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT C.content, C.DOC, U.f_name FROM Comment AS C, Users AS U WHERE picture_id IN (SELECT picture_id FROM Associate WHERE Hashtag = '{0}') AND C.users_id = U.users_id".format(
                    row[2]))
            temp = cursor.fetchall()
            cursor.execute(
                "SELECT COUNT(users_id) FROM Liketable WHERE picture_id = '{0}' AND users_id = '{1}'".format(row[2],
                                                                                                             uid))
            likecount = cursor.fetchall()
            cursor.execute("SELECT COUNT(picture_id) FROM Liketable WHERE picture_id = '{0}'".format(row[2]))
            like = cursor.fetchall()
            print(like)
            for l in likecount:
                if l[0] is not None:
                    if l[0] > 0:
                        for l1 in like:
                            if l1[0] is not None:
                                if not all.__contains__((row[0], row[1], row[2], row[3], "True", l1[0])):
                                    all.append((row[0], row[1], row[2], row[3], "True", l1[0]))
                            else:
                                if not all.__contains__((row[0], row[1], row[2], row[3], "True", 0)):
                                    all.append((row[0], row[1], row[2], row[3], "True", 0))

                    else:
                        for l1 in like:
                            if l1[0] is not None:
                                print(l1[0])
                                if not all.__contains__((row[0], row[1], row[2], row[3], "False", l1[0])):
                                    all.append((row[0], row[1], row[2], row[3], "False", l1[0]))
                            else:
                                if not all.__contains__((row[0], row[1], row[2], row[3], "False", 0)):
                                    all.append((row[0], row[1], row[2], row[3], "False", 0))

            for c in temp:
                if c[0] is not None:
                    com.append((c[0], c[1], c[2]))

    allnew = []
    for row in all:
        if row[3] is not None:
            temp = str(row[3])
            temp = "/static/" + temp + "_"
            allnew.append((str(row[0]), str(row[1]), str(row[2]), temp, row[4], row[5]))

    for row in user_activity:
        if row[0] is not None:
            u.append((row[0], row[1]))

    return render_template('home.html',name=uname, pop=a, user_activity=u, all_photos=allnew, comments=com)

@app.route("/friends", methods=['GET','POST'])
@flask_login.login_required
def friendlist():
    conn = mysql.connect()
    cursor = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute("SELECT f_name, l_name, email FROM Users WHERE users_id IN (SELECT users_id2 FROM Friendship WHERE users_id1 = '{0}')".format(uid))
    rows = cursor.fetchall()
    print(rows)
    cursor = conn.cursor()
    cursor.execute("SELECT f_name, l_name, email FROM Users WHERE users_id IN (SELECT Fr2.users_id2 FROM Friendship AS Fr1, Friendship AS Fr2 WHERE Fr1.users_id1 = '{0}' AND Fr2.users_id1 = Fr1.users_id2 AND Fr2.users_id2 NOT IN (SELECT Friendship.users_id2 FROM Friendship WHERE Friendship.users_id1 = '{0}') AND Fr2.users_id2 != '{0}')".format(uid))
    friend_of_friend = cursor.fetchall()
    fr = []
    frf = []
    for row1 in rows:
        if row1[0] is not None:
            fr.append((row1[0], row1[1], row1[2]))
    countf = 0
    for row in friend_of_friend:
        if row[0] is not None and countf <= 5:
            frf.append((row[0], row[1], row[2]))
            countf = countf+1
    return render_template('showFriends.html', friends=fr, friendf=friend_of_friend)

@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def profile():
    if request.method == 'GET':
        conn = mysql.connect()
        cursor = conn.cursor()
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor.execute("SELECT a_name FROM Album WHERE users_id ='{0}'".format(uid))
        rows = cursor.fetchall()
        alb = []
        for row1 in rows:
            if row1[0] is not None:
                alb.append(row1[0])
        conn.commit()
        return render_template('hello.html', albums=alb)
    else:
        album = request.form.get('Album')
        print(album)
        conn = mysql.connect()
        cursor = conn.cursor()
        uid = getUserIdFromEmail(flask_login.current_user.id)

        cursor.execute("SELECT a_id FROM Album WHERE a_name ='{0}' AND users_id = '{1}'".format(album, uid))
        rows = cursor.fetchall()
        for row in rows:
            if row[0] is not None:
                cursor.execute("SELECT imgdata, caption, picture_id FROM Pictures WHERE picture_id IN (SELECT picture_id FROM APassoc WHERE a_id='{0}')".format(row[0]))

        rows = cursor.fetchall()
        abc = str(uid)

        img = []
        com = []
        likes = []
        for row in rows:
            if row[0] is not None:
                # img.insert(0,send_from_directory(app.config['UPLOAD_FOLDER'], abc + '_' + str(row[0])))
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT C.content, C.DOC, U.f_name FROM Comment AS C, Users AS U WHERE picture_id = '{0}' AND C.users_id = U.users_id".format(row[2]))
                temp = cursor.fetchall()
                conn.commit()
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(users_id) FROM Liketable WHERE picture_id='{0}' AND users_id = '{1}'".format(row[2], uid))
                likecount = cursor.fetchall()
                conn.commit()
                conn = mysql.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(picture_id) FROM Liketable WHERE picture_id = '{0}'".format(row[2]))
                like = cursor.fetchall()
                conn.commit()
                print(like)

                for l in likecount:
                    if l[0] is not None:
                        if l[0] > 0:
                            for l1 in like:
                                if l1[0] is not None:
                                    img.append((row[0], row[1], row[2], "True", l1[0]))
                                else:
                                    img.append((row[0], row[1], row[2], "True", 0))

                        else:
                            for l1 in like:
                                if l1[0] is not None:
                                    img.append((row[0], row[1], row[2], "False", l1[0]))
                                else:
                                    img.append((row[0], row[1], row[2], "False", 0))
                for c in temp:
                    if c[0] is not None:
                        com.append((c[0], c[1], c[2]))
            print(img)

        conn.commit()
        return render_template('photos.html', photos=img, comments=com, url='/static/' + abc + '_', album=album)


UPLOAD_FOLDER = 'C:/Users/abhis/Downloads/PhotoShare/PhotoShare/static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# Test Showing Photos

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        a_name = request.form.get('albumName')
        a_name1 = request.form.get('albumN')
        check = request.form.get('check')

        tagged = request.form.get('tag')
        tagged = str.strip(tagged, ' ')
        print(check)
        print(a_name)
        print(tagged)
        tags = str.split(tagged, ' ')
        print(tags)
        abc = str(uid)
        #app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + "/" + uid
        ts = datetime.datetime.now()
        if imgfile and allowed_file(str(ts) + imgfile.filename):
            filename = secure_filename(str(ts) + imgfile.filename)
            imgfile.save(os.path.join(app.config['UPLOAD_FOLDER'], abc + '_' + filename))

        cursor = conn.cursor()
        cursor1 = conn.cursor()
        filename = secure_filename(str(ts) + imgfile.filename)
        query = "INSERT INTO Pictures (imgdata, users_id, caption) VALUES (%s, %s, %s)"
        cursor.execute(query, (filename, uid, caption))
        conn.commit()

        if check == 'true':
            query = "INSERT INTO Album (a_name, users_id) VALUES (%s, %s)"
            cursor.execute(query, (a_name, uid))
            conn.commit()
        else:
            a_name = a_name1
        cursor.execute("SELECT picture_id FROM Pictures WHERE imgdata=%s;", filename)
        rows = cursor.fetchall()
        print(rows)
        conn.commit()
        print(a_name)
        cursor1.execute("SELECT a_id FROM Album WHERE a_name=%s;", a_name)
        rows2 = cursor1.fetchall()
        print(rows2)
        conn.commit()
        query = "INSERT INTO APassoc (a_id, picture_id) VALUES (%s, %s)"
        cursor.execute(query, (rows2[0], rows[0]))
        conn.commit()
        for tag in tags:
            if tag[0] is not None:
                query = "INSERT INTO ASSOCIATE (picture_id, Hashtag) VALUES (%s, %s)"
                cursor.execute(query, (rows[0], tag))
        conn.commit()

        return redirect(url_for('profile'))
    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('album.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)
# end photo uploading code


@app.route("/exists_tags/<tagsearch>")
@flask_login.login_required
def exists_tags(tagsearch):
    conn = mysql.connect()
    cursor = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    positive_tag = []
    #positive_name = []
    all = []
    self = []
    #likes =0
    com = []
    com1 = []
    tagsearch = str.strip(tagsearch, ' ')
    namesearch = tagsearch

    tagsearch = str.split(tagsearch, ' ')
    tagsearch = str.strip(str(tagsearch), '[')
    tagsearch = str.strip(tagsearch, ']')
    tagsearch = str.strip(tagsearch, "'")
    tagsearch = str.split(tagsearch, "', '")
    for tag in tagsearch:
        if cursor.execute("SELECT DISTINCT (Hashtag) FROM Associate WHERE Hashtag =%s;", tag):
            rows = cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                    positive_tag.append(row[0])

            cursor = conn.cursor()
            cursor.execute("SELECT imgdata, caption, picture_id, users_id FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Associate WHERE Hashtag = '{0}')".format(tag)) #ALL photos with given tag
            rows = cursor.fetchall()
            print(rows)
            for row in rows:
                if row[0] is not None:
                    print("/static/"+str(row[3])+"_")
                    cursor = conn.cursor()
                    cursor.execute("SELECT C.content, C.DOC, U.f_name FROM Comment AS C, Users AS U WHERE picture_id IN (SELECT picture_id FROM Associate WHERE Hashtag = '{0}') AND C.users_id = U.users_id".format(tag))
                    temp = cursor.fetchall()
                    cursor.execute("SELECT COUNT(users_id) FROM Liketable WHERE picture_id = '{0}' AND users_id = '{1}'".format(row[2], uid))
                    likecount = cursor.fetchall()
                    cursor.execute("SELECT COUNT(picture_id) FROM Liketable WHERE picture_id = '{0}'".format(row[2]))
                    like = cursor.fetchall()
                    print(like)
                    for l in likecount:
                        if l[0] is not None:
                            if l[0] > 0:
                                for l1 in like:
                                    if l1[0] is not None:
                                        if not all.__contains__((row[0], row[1], row[2], row[3], "True", l1[0])):
                                            all.append((row[0], row[1], row[2], row[3], "True", l1[0]))
                                    else:
                                        if not all.__contains__((row[0], row[1], row[2], row[3], "True", 0)):
                                            all.append((row[0], row[1], row[2], row[3], "True", 0))

                            else:
                                for l1 in like:
                                    if l1[0] is not None:
                                        print(l1[0])
                                        if not all.__contains__((row[0], row[1], row[2], row[3], "False", l1[0])):
                                            all.append((row[0], row[1], row[2], row[3], "False", l1[0]))
                                    else:
                                        if not all.__contains__((row[0], row[1], row[2], row[3], "False", 0)):
                                            all.append((row[0], row[1], row[2], row[3], "False", 0))

                    for c in temp:
                        if c[0] is not None:
                            com.append((c[0], c[1], c[2]))


            cursor = conn.cursor()
            cursor.execute("SELECT imgdata, caption, picture_id FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Associate WHERE Hashtag = '{0}') AND users_id = '{1}'".format(tag, uid))    #Only current User's photos with given tag
            rows = cursor.fetchall()
            for row in rows:
                if row[0] is not None:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT C.content, C.DOC, U.f_name FROM Comment AS C, Users AS U WHERE picture_id  = '{0}' AND C.users_id = U.users_id".format(row[2]))
                    temp = cursor.fetchall()
                    cursor.execute("SELECT COUNT(users_id) FROM Liketable WHERE picture_id ='{0}' AND users_id = '{1}'".format(row[2], uid))
                    likecount = cursor.fetchall()
                    print(likecount)
                    cursor.execute(
                        "SELECT COUNT(picture_id) FROM Liketable WHERE picture_id  = '{0}'".format(row[2]))
                    like = cursor.fetchall()

                    for l in likecount:
                        if l[0] is not None:
                            if l[0] > 0:
                                for l1 in like:
                                    if l1[0] is not None:
                                        if not self.__contains__((row[0], row[1], row[2], "True", l1[0])):
                                            self.append((row[0], row[1], str(row[2]) + "_", "True", l1[0]))
                                    else:
                                        if not self.__contains__((row[0], row[1], row[2], "True", 0)):
                                            self.append((row[0], row[1], str(row[2]) + "_", "True", 0))

                            else:
                                for l1 in like:
                                    if l1[0] is not None:
                                        if not self.__contains__((row[0], row[1], row[2], "False", l1[0])):
                                            self.append((row[0], row[1], str(row[2]) + "_", "False", l1[0]))
                                    else:
                                        if not self.__contains__((row[0], row[1], row[2], "False", 0)):
                                            self.append((row[0], row[1], str(row[2]) + "_", "False", 0))

                    for c in temp:
                        if c[0] is not None:
                            com1.append((c[0], c[1], c[2]))

    frows = None
    newfrows = []
    frornot = False
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "SELECT f_name, l_name, email, users_id FROM Users WHERE f_name = '{0}'"
    cursor.execute(query.format(namesearch))
    frows = cursor.fetchall()
    for row in frows:
        if row[0] is not None:
           newfrows.append((row[0], row[1], row[2], row[3]))
           cursor.execute("SELECT users_id2 FROM Friendship WHERE users_id1 = '{0}' AND users_id2 = '{1}'".format(uid, row[3]))
           t = cursor.fetchall()
           for t1 in t:
               if t1[0] is not None:
                  if t1[0] != ():
                      frornot = True
                  else:
                      frornot = False
               print(frornot)
    abc = str(uid)
    tags = ""
    if positive_tag is not None:
        for tag in tagsearch:
            tags = tags + " " + tag
        tags = str.strip(tags, ' ')
        tags = "'" + tags + "'"
    allnew = []
    for row in all:
        if row[3] is not None:
            temp = str(row[3])
            temp = "/static/" + temp + "_"
            allnew.append((str(row[0]), str(row[1]), str(row[2]), temp, row[4], row[5]))

    if frows is not None:
        return render_template('exists_tag.html', searchtag=tags, all_photos=allnew, self_photos=self, friends=newfrows,
                               url='/static/' + abc + '_', comment=com, comment1=com1, frornot=frornot)
    else:
        return render_template('exists_tag.html', searchtag=tags, all_photos=allnew, self_photos=self,
                               url='/static/' + abc + '_', comment=com, comment1=com1)

@app.route("/search_tags", methods=['GET', 'POST'])
@flask_login.login_required
def search_tags():
    if request.method == 'POST':
        tagsearch = request.form['search']
        return redirect(url_for('exists_tags', tagsearch=tagsearch))
    else:
        return redirect(url_for('home'))
        #tagsearch = request.args.get('tagsearch')
        #return redirect(url_for('exists_tags', tagsearch=tagsearch))

#@app.route("/popular_tags", methods=['GET', 'POST'])
def popular_tags():
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT (Hashtag) FROM Associate GROUP BY Hashtag ORDER BY COUNT(*) DESC LIMIT 3")
    return cursor.fetchall()  # Returns top three most popular tags in poptags

@app.route("/add_comment", methods=['GET', 'POST'])
@flask_login.login_required
def add_comment():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        pic_id = request.form['pic_id']
        liked = request.form['like']
        print(liked)

        comment = request.form.get('comment')
        conn = mysql.connect()
        cursor = conn.cursor()
        ts = datetime.datetime.now()
        if comment!="" and comment!=None:
            cursor.execute("INSERT INTO Comment(content, DOC, users_id, picture_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment, ts, uid, pic_id))
            conn.commit()
            #cursor.execute("SELECT content FROM Comment")
            #rows = cursor.fetchall()

        if liked == "true":
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Liketable(users_id, picture_id, DOC) VALUES ('{0}', '{1}', '{2}')".format(uid, pic_id, ts))
            conn.commit()
        else:
            print("chkpt")
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Liketable WHERE users_id = '{0}' AND picture_id = '{1}'".format(uid, pic_id))
            conn.commit()
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('home'))


@app.route("/add_like", methods=['GET', 'POST'])
@flask_login.login_required
def add_like(pic_id):  ###########Needs "picture_id" as argument############
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    if cursor.execute(
            "SELECT Pictures.picture_id FROM Pictures WHERE Pictures.pictures_id = '{0}' AND Pictures.users_id = '{1}'".format(
                        pic_id, uid)):
        print("Illegal")
        ##################DISPLAY ON SCREEN: YOU CANNOT LIKE YOUR OWN PHOTOS
    else:
        cursor = conn.cursor()
        ts = datetime.datetime.now().timestamp()
        cursor.execute(
                "INSERT INTO Liketable(users_id, picture_id, DOC) VALUES ('{0}', '{1}', '{2}')".format(
                    uid, pic_id, ts))
        cursor.commit()
    return redirect(url_for('showAlbum'))


@app.route("/friend_reco/", methods=['GET', 'POST'])
@flask_login.login_required
def friend_reco():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("SELECT Fr2.users_id2 FROM Friendship AS Fr1, Friendship AS Fr2 WHERE Fr1.users_id1 = '{0}' AND Fr2.users_id1 = Fr1.users_id2 AND Fr2.users_id2 NOT IN (SELECT Friendship.users_id2 FROM Friendship WHERE Friendship.users_id1 = '{1}')".format(uid, uid))
        friend_of_friend = cursor.fetchall()
        return render_template('friend_reco.html', friends=friend_of_friend)
    else:
        return redirect(url_for('home'))


# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('main.html', message='Welcome to Photoshare')


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
