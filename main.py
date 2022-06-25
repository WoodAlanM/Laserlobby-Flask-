from flask import Flask, flash, render_template, Response, request, redirect, jsonify
import urllib.request
import os
from os.path import join, dirname, realpath
import json
import cv2
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user, login_user, logout_user
from models import UserModel,db,login
import numpy as np
from PIL import Image, ImageOps
import codecs

app = Flask(__name__)

db.init_app(app)
login.init_app(app)
login.login_view = 'login'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

BASEDIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = 'static/uploads/temp/'
USERS_FOLDER = 'static/users/'

GRAY_LIST = []

app.secret_key = "thekeytosuccessissweat"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'JPG', 'JPEG', 'PNG'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Initializes database if it has not been created
@app.before_first_request
def create_table():
    db.create_all()


@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/editor')
     
    if request.method == 'POST':
        email = request.form['email']
        user = UserModel.query.filter_by(email = email).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            return redirect('/editor')
     
    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect('/editor')
     
    if request.method == 'POST':
        first_name = request.form['first']
        last_name = request.form['last']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
 
        if UserModel.query.filter_by(email=email).first():
            return ('Email already in use.')
            if UserModel.query.filter_by(username=username).first():
                return ('Username already in use.')
    
        # Make directory for user
        os.mkdir(os.path.join(BASEDIR, USERS_FOLDER, username))
        # Make canvases, grays, and temp folder for each user
        os.mkdir(os.path.join(BASEDIR, USERS_FOLDER, username, 'canvases'))
        os.mkdir(os.path.join(BASEDIR, USERS_FOLDER, username, 'grays'))
        os.mkdir(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp'))

        user = UserModel(first_name=first_name, last_name=last_name, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/editor')
@login_required
def editor():
    return render_template('editor.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/')
@login_required
def index():
    return render_template('login.html')


# Uploads image to server.
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    username = current_user.username
    if 'file' not in request.files:
        print('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        print('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp', filename))
        # This is where the image will be turned into greyscale
        # Image is read into opencv
        image = cv2.imread(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp', filename))
        # Image is converted to greyscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # working directory is changed
        os.chdir(os.path.join(BASEDIR, USERS_FOLDER, username, 'grays'))
        # opencv saves the greyscale version
        cv2.imwrite(filename, gray)
        # original image is deleted
        os.remove(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp', filename))
        return filename
    else:
        print('Allowed image types are - png, jpg, jpeg')
        return redirect(request.url)


# Uploads image to server AND removes background.
@app.route('/upload_image_rb', methods=['POST'])
@login_required
def upload_image_rb():
    username = current_user.username
    if 'file' not in request.files:
        print('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        print('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp', filename))
        # This is where the image will be turned into greyscale
        # Image is read into opencv
        image = cv2.imread(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp', filename))
        # Image is converted to greyscale
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # working directory is changed
        os.chdir(os.path.join(BASEDIR, USERS_FOLDER, username, 'grays'))
        #new stuff starts here
        #get height and width of image
        height, width, channels = image.shape
        #create mask, not really sure what this does
        mask = np.zeros(image.shape[:2],np.uint8)
        #also not sure about these two lines
        bgdModel = np.zeros((1,65),np.float64)
        fgdModel = np.zeros((1,65),np.float64)
        #probably makes a rectangle
        rect = (1,1,width,height)
        cv2.grabCut(image,mask,rect,bgdModel,fgdModel,5,cv2.GC_INIT_WITH_RECT)
        #not sure about any of this, but the next wo lines makes a black
        #area where the fish is
        mask2 = np.where((mask==2)|(mask==0),1,0).astype('uint8')
        img = image*mask2[:,:,np.newaxis]
        #this line reverses that image to make everything else black
        _,alpha = cv2.threshold(img,0,255,cv2.THRESH_BINARY_INV)
        # this defines blacks and grays        
        black_lo=np.array([0,0,0])
        black_hi=np.array([86,86,86])
        # this makes a mask based on the black background
        # Mask image to only select browns
        mask=cv2.inRange(alpha,black_lo,black_hi)
        # this changes the masked part to green
        # Change image to green where we found brown
        image[mask>0]=(144,238,144)
        cv2.imwrite('temp.png', image)
        # Open with PIL
        img = Image.open('temp.png')
        # convert to rgba
        rgba_image = img.convert('RGBA')
        #   get data about image
        datas = rgba_image.getdata()
        # this switches all the green to transparent
        newData = []
        for item in datas:
            if item[0] == 144 and item[1] == 238 and item[2] == 144:
                newData.append((255, 255, 255, 0)) # This is for checking white pixels, replace transparent. Do
                # if item[3] == 0 to check for transparent pixels.
            else:
                newData.append(item)
        rgba_image.putdata(newData)
        # changes rgba image to grayscale which brings back the white background
        gray_image = ImageOps.grayscale(rgba_image)
        gray_image.save('tempgray.jpg', 'PNG')
        grayimg = Image.open('tempgray.jpg')
        rgba_gray = grayimg.convert('RGBA')
        datas_for_gray = rgba_gray.getdata()
        newDataForGray = []
        # converts white to transparent
        for item in datas_for_gray:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newDataForGray.append((255, 255, 255, 0)) # This is for checking white pixels, replace transparent. Do
                # if item[3] == 0 to check for transparent pixels.
            else:
                newDataForGray.append(item)
        rgba_gray.putdata(newDataForGray)
        #saves file to grays folder
        rgba_gray.save(filename, 'PNG')
        # original and temp images are deleted
        os.remove(os.path.join(BASEDIR, USERS_FOLDER, username, 'temp', filename))
        os.remove(os.path.join(BASEDIR, USERS_FOLDER, username, 'grays', 'temp.png'))
        os.remove(os.path.join(BASEDIR, USERS_FOLDER, username, 'grays', 'tempgray.jpg'))
        return filename
    else:
        print('Allowed image types are - png, jpg, jpeg')
        return redirect(request.url)


@app.route('/fill_list', methods=['POST'])
@login_required
def fill_list():
    for (root,dirs,files) in os.walk(os.path.join(BASEDIR, USERS_FOLDER, current_user.username, 'grays')):
        for name in files:
            if not name in GRAY_LIST:
                GRAY_LIST.append(name)
    gray_list_string = "!and!".join(GRAY_LIST)
    return gray_list_string


@app.route('/save_canvas_json', methods=['POST'])
@login_required
def save_canvas_json():
    save_json = request.get_json(force=True)
    with open('data.json', 'w') as out_file:
        json.dump(save_json, out_file, sort_keys = True, indent = 4, ensure_ascii = False)
    return "saved"


@app.route('/load_canvas_json', methods=['POST'])
@login_required
def load_canvas_json():
    # Change so a name for the canvas needs to be entered
    filename = os.path.join(BASEDIR, USERS_FOLDER, current_user.username, 'cavnases', 'data.json')
    with open(filename) as json_file:
        data = json.load(json_file)
    return data


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    if request.method == 'POST':
        current_id = current_user.id
        user = UserModel.query.filter_by(id=current_id).first()
        email = request.form['email']
        username = request.form['username']
        first = request.form['first']
        last = request.form['last']
        if first:
            user.first = first
        if last:
            user.last = last
        if username:
            user.username = username
        if email:
            user.email = email
        db.session.commit()
        return redirect('/profile')
    return render_template('profile.html')


@app.route('/get_user_username', methods=['POST'])
@login_required
def get_user_username():
    username = current_user.username
    return str(username)


@app.route('/get_user_email', methods=['POST'])
@login_required
def get_user_email():
    email = current_user.email
    return str(email)


@app.route('/get_user_first_name', methods=['POST'])
@login_required
def get_user_first_name():
    first = current_user.first_name
    return str(first)


@app.route('/get_user_last_name', methods=['POST'])
@login_required
def get_user_last_name():
    last = current_user.last_name
    return str(last)


if __name__ == '__main__':
    
    app.run(host="0.0.0.0", port=80)