from flask import Flask, request, render_template, redirect, url_for, make_response, send_from_directory
from pymongo import MongoClient
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 비밀 키 설정

client = MongoClient("mongodb+srv://ambition:ambition@cluster0.oycph.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") 
db = client['ambition']
members_collection = db['members']

serializer = URLSafeTimedSerializer(app.secret_key)

@app.route('/')
def index():
    email_cookie = request.cookies.get('email')
    if email_cookie:
        try:
            email = serializer.loads(email_cookie, max_age=60*60*24*30)  # 쿠키 유효기간 30일
            member = members_collection.find_one({'email': email})
            if member:
                if 'stamp' not in member:
                    member['stamp'] = 0
                return render_template('mypage.html', member=member)
        except:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/find')
def find_choice():
    return render_template('choice.html')

@app.route('/map/<tag>')
def map(tag):
    return render_template('map.html', tag=tag)

@app.route('/stampimg')
def stampimg():
    return send_from_directory('static', 'stamp.png')

@app.route('/mypage')
def mypage():
    email_cookie = request.cookies.get('email')
    if email_cookie:
        try:
            email = serializer.loads(email_cookie, max_age=60*60*24*30)  # 쿠키 유효기간 30일
            member = members_collection.find_one({'email': email})
            if member:
                if 'stamp' not in member:
                    member['stamp'] = 0
                return render_template('mypage.html', member=member)
        except:
            return render_template('login.html')  # 수정된 부분
    return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        member = members_collection.find_one({'email': request.form['email']})
        if member:
            if member['password'] == request.form['password']:
                response = make_response(redirect(url_for('mypage')))
                email_cookie = serializer.dumps(request.form['email'])
                response.set_cookie('email', email_cookie, max_age=60*60*24*30)  # 쿠키 유효기간 30일
                return response
            return render_template('login.html', error=401)
        return render_template('login.html', error=404)
    return render_template('login.html', error=0)

@app.route('/join', methods=['POST', 'GET'])
def join():
    if request.method == 'POST':
        member = members_collection.find_one({'email': request.form['email']})
        if member:
            return render_template('join.html', error=409)
        member_info = {
            'email': request.form['email'],
            'password': request.form['password'],
            'name': request.form['username'],
            'stamp' : 0
        }
        members_collection.insert_one(member_info)
        return redirect(url_for('login'))
    return render_template('join.html')

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('email')
    return response

@app.route('/market')
def market():
    products = [
        {'name': 'Product 1', 'description': 'Description 1', 'price': '10', 'image_url': '/static/images/product1.jpg'},
        {'name': 'Product 2', 'description': 'Description 2', 'price': '20', 'image_url': '/static/images/product2.jpg'},
        {'name': 'Product 3', 'description': 'Description 3', 'price': '30', 'image_url': '/static/images/product3.jpg'}
    ]
    return render_template('market.html', products=products)

@app.route('/buy/<product_name>/<product_price>')
def buy(product_name, product_price):
    email_cookie = request.cookies.get('email')
    if email_cookie:
        email = serializer.loads(email_cookie, max_age=60*60*24*30)  # 쿠키 유효기간 30일
        member = members_collection.find_one({'email': email})
        if member:
            product_price = int(product_price.replace('개', ''))
            if member['stamp'] < product_price:
                return redirect(url_for('market'))
            
            # 상품 이름과 가격이 일치하는지 확인
            products = [
                {'name': 'Product%201', 'description': 'Description 1', 'price': 10},
                {'name': 'Product%202', 'description': 'Description 2', 'price': 20},
                {'name': 'Product%203', 'description': 'Description 3', 'price': 30}
            ]
            product = next((p for p in products if p['name'] == product_name and p['price'] == product_price), None)
            
            if product:
                # 스탬프 차감
                members_collection.update_one({'email': email}, {'$inc': {'stamp': -product_price}})
                return redirect(url_for('market'))
            else:
                return redirect(url_for('market'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)