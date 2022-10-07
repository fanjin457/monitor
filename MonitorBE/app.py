from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import LONGTEXT
import uuid
import requests
import json

app = Flask(__name__)

# 设置可以跨域访问
CORS(app, supports_credentials=True)

# key是用户名，value是token
username_tokens = {}

# 数据库
# mysql+pymysql://用户名:密码@IP地址:端口号/数据库名
db_uri = 'mysql+pymysql://{}:{}@{}:{}/{}'\
    .format('root', 'wwh802613', '127.0.0.1', 3306, 'yinhangjihua')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 创建数据库实例
db = SQLAlchemy(app)
# 用来访问数据库
# engine = db.get_engine()


# 定义数据模型
class AlarmEvent(db.Model):
    __tablename__ = 'alarm_event'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(LONGTEXT)
    create_time = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))
    result = db.Column(db.Text)


# 关联表信息
db.create_all()


# 登录接口
@app.route('/user/login', methods=['GET', 'POST'])
def login():
    # 发送客户端发送的用户名、密码参数
    username = request.json.get('username')
    password = request.json.get('password')

    # TODO 正常做法：去数据库中查询用户名、密码是否正确
    if 'wwh666' != username:
        return {
            'code': 4000,
            'msg': '用户名错误'
        }

    if 'wwh666' != password:
        return {
            'code': 4001,
            'msg': '密码错误'
        }

    # 使用uuid作为token
    token = str(uuid.uuid1())
    username_tokens[username] = token
    # print(username_tokens)
    return {
        'msg': '登陆成功',
        'data': {
            'token': token
        }
    }


# 退出登录接口
@app.route('/logout', methods=['POST'])
def logout():
    if not username_tokens:
        return {
            'code': 0,
            'msg': '退出登录成功'
        }

    # 从请求头中获取用户的token信息
    token = request.headers.get('Token')
    # 根据token找到用户名
    username = ''
    for key, value in username_tokens.items():
        if value == token:
            username = key
            break
    # 删除token
    del username_tokens[username]
    return {
        'code': 0,
        'msg': '退出登录成功'
    }


# 查询所有的事件数据
@app.route('/event')
def event():
    # 从请求头中获取用户的token信息
    token = request.headers.get('Token')
    exists = False
    for key, value in username_tokens.items():
        if value == token:
            exists = True
            break

    # token不存在
    if not exists:
        return {
            'code': 4002,
            'msg': 'Token无效'
        }

    # 查询数据库
    # data = db.session.query(AlarmEvent).all()
    data = db.session.query(AlarmEvent).order_by(AlarmEvent.id.desc()).all()
    # limit 0,5
    # data = db.session.query(AlarmEvent).offset(0).limit(5).all()
    # data = db.session.query(AlarmEvent).filter(AlarmEvent.image == '200').all()
    # with engine.connect() as conn:
    #     ret = conn.execute('SELECT * FROM alarm_event')
    #     # 返回的是元组列表，无法转换成json
    #     # [(), (), ()]
    #     data = ret.fetchall()

    # 元组列表 -> 字典列表
    new_data = []
    for evt in data:
        new_data.append({
            'id': evt.id,
            'image': evt.image,
            'create_time': str(evt.create_time),
            'result': evt.result
        })

    return {
        'code': 0,
        'data': new_data
    }


# 接收客户端发送的图片数据，进行图像解析
@app.route('/test', methods=['POST'])
def test():
    # 从请求头中获取用户的token信息
    token = request.headers.get('Token')
    # print(token)
    # print(username_tokens)
    exists = False
    for key, value in username_tokens.items():
        if value == token:
            exists = True
            break

    # token不存在
    if not exists:
        return {
            'code': 4002,
            'msg': 'Token无效'
        }

    # token存在
    # 获取客户端发送的图片数据
    image_base64 = request.json.get('image')
    # 去掉base64头部：data:image/png;base64,
    image_base64 = image_base64[image_base64.find(',') + 1:]
    # TODO 调用算法对图像进行解析
    # print(image_base64)

    # 获取access_token
    # https://aip.baidubce.com/oauth/2.0/token
    # grant_type: 固定值client_credentials
    # client_id: api_key
    # client_secret: secret_key
    resp = requests.post('https://aip.baidubce.com/oauth/2.0/token', {
        'grant_type': 'client_credentials',
        'client_id': 'qztv6Zi67XdGwwMcfd58R3Zp',
        'client_secret': '19RMgM7Ss6sadVTfq5vMaxfRgy7aYb5j'
    })
    print(resp.json()['access_token'])

    # 调用算法接口
    # https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/weapon01
    # access_token：url参数
    # url：图片的路径（需要增加一个url参数input_type=url）
    # image：图片数据

    # url_params = '?input_type=url&access_token=' + resp.json()['access_token']
    # resp = requests.post('https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/weapon01' + url_params, json={
    #     'url': 'https://t00img.yangkeduo.com/goods/images/2020-03-10/4d0b43ae-3f07-4d29-a064-e73fa580ce20.jpg'
    # })
    # print(resp.json())

    url_params = '?access_token=' + resp.json()['access_token']
    resp = requests.post('https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/weapon01' + url_params, json={
        'image': image_base64
    })
    print(resp.json())

    # 算法的识别结果
    results = resp.json()['results']
    if results:  # 有危险物品
        # 添加数据到数据库
        # 这里需要将results数组（列表）对象，转成JSON字符串
        evt = AlarmEvent(image=image_base64, result=json.dumps(results))
        db.session.add(evt)
        db.session.commit()  # 提交事务
        return {
            'code': 0,
            'data': results
        }
    else:  # 没有危险物品
        # 添加数据到数据库
        evt = AlarmEvent(image=image_base64)
        db.session.add(evt)
        db.session.commit()
        return {
            'code': 0,
            'msg': '没有识别到危险物品'
        }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)