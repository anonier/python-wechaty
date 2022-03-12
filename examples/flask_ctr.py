import json
import robot
import flask
from flask import request
from wechaty import (
    MessageType,
    FileBox,
    Wechaty,
    Contact,
    Room,
    Message,
    Image as WeImage,
    Friendship,
    FriendshipType,
    EventReadyPayload
)

server = flask.Flask(__name__)


@server.route('/login', methods=['get', 'post'])
def login():
    # 获取通过url请求传参的数据
    username = request.values.get('name')
    # 获取url请求传的密码，明文
    pwd = request.values.get('pwd')
    # 判断用户名、密码都不为空，如果不传用户名、密码则username和pwd为None
    if username and pwd:
        if username == 'xiaoming' and pwd == '111':
            resu = {'code': 200, 'message': '登录成功'}
            return json.dumps(resu, ensure_ascii=False)  # 将字典转换为json串, json是字符串
        else:
            resu = {'code': -1, 'message': '账号密码错误'}
            return json.dumps(resu, ensure_ascii=False)
    else:
        resu = {'code': 10001, 'message': '参数不能为空！'}
        return json.dumps(resu, ensure_ascii=False)
    from_contact: Contact = msg.talker()
    room: Optional[Room] = msg.room()
    await conversation.ready()
    conversation: Union[
        Room, Contact] = from_contact if room is None else room
    await conversation.ready()
    await conversation.say('@' + msg.talker().name + ' 请查看' + insurance + '的电子保单文件!')


if __name__ == '__main__':
    server.run(debug=True, port=8888, host='0.0.0.0')
