"""example code for ding-dong-bot with oop style"""
import asyncio
import base64
import json
import os
import random
import re
import time
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Union

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
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
from wechaty_puppet import get_logger

from task import Task

logger = get_logger(__name__)


async def main() -> None:
    """doc"""
    bot = MyBot().use(Task())
    os.environ['WECHATY_PUPPET'] = 'wechaty-puppet-padlocal'
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '192.168.1.124:8788'
    await bot.start()


# 25398111924@chatroom
ip = 'http://192.168.1.114/'
# 21121012651@chatroom
ip_js = 'http://192.168.1.111/'


class MyBot(Wechaty):
    """
    listen wechaty event with inherited functions, which is more friendly for
    oop developer
    """

    def __init__(self) -> None:
        """initialization function
        """
        self.login_user: Optional[Contact] = None
        super().__init__()

    async def on_ready(self, payload: EventReadyPayload) -> None:
        """listen for on-ready event"""
        logger.info('ready event %s...', payload)

    async def on_message(self, msg: Message) -> None:
        """
        listen for message event
        """
        from_contact: Contact = msg.talker()
        contact_id = from_contact.contact_id
        text: str = msg.text()
        room: Optional[Room] = msg.room()
        room_id = room.room_id
        msg_type: MessageType = msg.type()

        if '25398111924@chatroom' == room_id:
            if '@AI出单' in text and '查单' not in text and '报价' not in text and text.count('出单') == 1 and '录单' not in text:
                conversation: Union[Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                await conversation.say('@' + msg.talker().name + ' 未识别到指令,请核实后重新发送!')

            elif '@AI出单' in text and '查单' in text:
                conversation: Union[Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/policy.do'
                x = text.split()
                man_cmd = [a for a in x if '业务员' in a]
                if len(x) != 4 or len(man_cmd) == 0 or (':' not in man_cmd[0] and '：' not in man_cmd[0]):
                    await conversation.say('@' + msg.talker().name + " 未识别到指令,请核实后重新发送!")
                    return
                salesman = man_cmd[0].split(':')[1] if ':' in man_cmd[0] else man_cmd[0].split('：')[1]
                car_licence = [a for a in x if '出单' not in a and '查单' not in a and '@' not in a and '业务员' not in a]
                if len(car_licence) == 0 or not_car_number(license_plate, car_licence[0]):
                    await conversation.say('@' + msg.talker().name + " 未识别到车辆信息,请核对信息!")
                    return
                car_licence = car_licence[0]
                await conversation.say('@' + msg.talker().name + " 收到查单指令,识别到车辆信息,数据处理中请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'operator': "1",
                        'cmdName': text,
                        'salesman': salesman,
                        'licenseId': car_licence,
                        'appKey': "X08ASKYS",
                        'nickname': msg.talker().name
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                except:
                    await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                    return
                res_dict = json.loads(response.text)
                if res_dict['errorCode'] != "":
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
                    return
                num = 0
                second = sleep_time(0, 0, 5)
                while True:
                    time.sleep(second)
                    url = ip + 'api/RobotApi/pullPolicy.do'
                    multipart_encoder = MultipartEncoder(
                        fields={
                            'uuid': res_dict['data'],
                            'appKey': "X08ASKYS"
                        },
                        boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                    )
                    headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                    try:
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                    except:
                        if num == 6:
                            await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if response_dict['errorCode'] != "":
                        await conversation.say('@' + msg.talker().name + response_dict['errorMsg'])
                        return
                    if num == 6:
                        await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                        return
                    elif response_dict['success']:
                        await conversation.say('@' + msg.talker().name + ' 请查看' + car_licence + '的电子保单文件!')
                        for key, value in response_dict['data'].items():
                            file_box = FileBox.from_url(
                                value,
                                name=key)
                            await conversation.say(file_box)
                        return
                    num = num + 1

            elif '@AI出单' in text and '报价' in text:
                conversation: Union[Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/declaration.do'
                x = text.split()
                insurance_cmd = [a for a in x if '险种' in a]
                man_cmd = [a for a in x if '业务员' in a]
                if (len(x) != 5 and len(x) != 7) or len(man_cmd) == 0 or len(insurance_cmd) == 0 \
                    or len(insurance_cmd) > 1 or (':' not in man_cmd[0] and '：' not in man_cmd[0]):
                    await conversation.say('@' + msg.talker().name + " 未识别到指令,请核实后重新发送!")
                    return
                salesman = man_cmd[0].split(':')[1] if ':' in man_cmd[0] else man_cmd[0].split('：')[1]
                insurance = insurance_cmd[0].split(':')[1] if ':' in insurance_cmd[0] else insurance_cmd[0].split('：')[
                    1]
                if '基本' in insurance:
                    if len(x) == 5:
                        if len([a for a in x if '-商业' in a]) != 0:
                            jqInsurance = 'true'
                            csInsurance = 'false'
                            szInsurance = None
                            driver = None
                            passenger = None
                            accident = None
                        else:
                            jqInsurance = 'false' if [a for a in x if '-交强' in a] else 'true'
                            if len([a for a in x if '-车损' in a]) != 0:
                                csInsurance = 'false'
                            elif len([a for a in x if '车损' in a and '-' not in a]) != 0:
                                csInsurance = get_number(a for a in x if '车损' in a)
                            else:
                                csInsurance = 'true'
                            szInsurance = '100' if len([a for a in x if '三者' in a]) == 0 else get_number(
                                str([a for a in x if '三者' in a]))
                            driver = '1' if len([a for a in x if '司机' in a]) == 0 else get_number(
                                str([a for a in x if '司机' in a]))
                            passenger = '1' if len([a for a in x if '乘客' in a]) == 0 else get_number(
                                str([a for a in x if '乘客' in a]))
                            accident = None if len([a for a in x if '意外' in a]) == 0 else get_number(
                                str([a for a in x if '意外' in a]))
                    elif len(x) == 7:
                        jqInsurance = 'true'
                        csInsurance = 'true'
                        szInsurance = get_number(str([a for a in x if '三者' in a]))
                        driver = get_number(str([a for a in x if '司机' in a]))
                        passenger = get_number(str([a for a in x if '乘客' in a]))
                        accident = None
                    else:
                        await conversation.say('@' + msg.talker().name + " 未识别到指令，请核实后重新发送!")
                        return
                elif '进阶' in insurance:
                    if len(x) == 5:
                        if len([a for a in x if '-商业' in a]) != 0:
                            jqInsurance = 'true'
                            csInsurance = 'false'
                            szInsurance = None
                            driver = None
                            passenger = None
                            accident = None
                        else:
                            jqInsurance = 'false' if [a for a in x if '-交强' in a] else 'true'
                            if len([a for a in x if '-车损' in a]) != 0:
                                csInsurance = 'false'
                            elif len([a for a in x if '车损' in a and '-' not in a]) != 0:
                                csInsurance = get_number(a for a in x if '车损' in a)
                            else:
                                csInsurance = 'true'
                            szInsurance = '150' if len([a for a in x if '三者' in a]) == 0 else get_number(
                                str([a for a in x if '三者' in a]))
                            driver = '5' if len([a for a in x if '司机' in a]) == 0 else get_number(
                                str([a for a in x if '司机' in a]))
                            passenger = '5' if len([a for a in x if '乘客' in a]) == 0 else get_number(
                                str([a for a in x if '乘客' in a]))
                            accident = None if len([a for a in x if '意外' in a]) == 0 else get_number(
                                str([a for a in x if '意外' in a]))
                    elif len(x) == 7:
                        jqInsurance = 'true'
                        csInsurance = 'true'
                        szInsurance = get_number(str([a for a in x if '三者' in a]))
                        driver = get_number(str([a for a in x if '司机' in a]))
                        passenger = get_number(str([a for a in x if '乘客' in a]))
                        accident = None
                    else:
                        await conversation.say('@' + msg.talker().name + " 未识别到指令，请核实后重新发送!")
                        return
                szInsurance = szInsurance[0]
                driver = driver[0]
                passenger = passenger[0]
                await conversation.say('@' + msg.talker().name + " 收到报价指令,努力处理中,请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'operator': "2",
                        'cmdName': text,
                        'appKey': "X08ASKYS",
                        'jqInsurance': jqInsurance,
                        'csInsurance': csInsurance,
                        'szInsurance': szInsurance,
                        'salesman': salesman,
                        'driver': driver,
                        'passenger': passenger,
                        'accident': None if accident is None else '*'.join(accident),
                        'nickname': msg.talker().name
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                except:
                    await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                    return
                res_dict = json.loads(response.text)
                if res_dict['errorCode'] != "":
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
                    return
                num = 0
                second = sleep_time(0, 0, 5)
                while True:
                    time.sleep(second)
                    url = ip + 'api/RobotApi/pullPolicy.do'
                    multipart_encoder = MultipartEncoder(
                        fields={
                            'uuid': res_dict['data'],
                            'appKey': "X08ASKYS"
                        },
                        boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                    )
                    headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                    try:
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                    except:
                        if num == 6:
                            await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if response_dict['errorCode'] != "":
                        await conversation.say('@' + msg.talker().name + response_dict['errorMsg'])
                        return
                    if num == 6:
                        await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                        return
                    elif response_dict['success']:
                        try:
                            data = response_dict['data']
                            await conversation.say(
                                '@' + msg.talker().name + ' 本车客户风险等级:'
                                + data['customerRiskRating'] + '; 车系风险等级:'
                                + data['familyGrade'] + '; 无赔系数:'
                                + data['unattendGrade'] + '; 自主定价系数:'
                                + data['rateProduct'] + '。')
                            await conversation.say(
                                '@' + msg.talker().name + ' '
                                + data['ownerName'] + '，您好！您的爱车'
                                + data['plateNumber'] + '预计估价共计'
                                + data['totalPremium'] + '元，其中交强险'
                                + data['compulsoryPremium'] + '元， 商业险'
                                + data['businessPremium'] + '元。商业险明细：车损保额'
                                + [a for a in data['policyBusinessCategoryList'] if "车损" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "车损" in a['name']][0][
                                    'premium'] + '元 ；三者保额'
                                + [a for a in data['policyBusinessCategoryList'] if
                                   "三者" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "三者" in a['name']][0][
                                    'premium'] + '元 ；司机保额'
                                + [a for a in data['policyBusinessCategoryList'] if "司机" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "司机" in a['name']][0][
                                    'premium'] + '元；乘客保额'
                                + [a for a in data['policyBusinessCategoryList'] if "乘客" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "乘客" in a['name']][0][
                                    'premium'] + '元 。代收车船税'
                                + data['taxPremium'] + '元。此报价仅供参考，最终价格以出单为准。')
                            file_box = FileBox.from_url(
                                data['url'],
                                name='policy.jpg')
                            await conversation.say(file_box)
                            return
                        except:
                            await conversation.say('@' + msg.talker().name + " 操作报价失败，请手动操作！")
                            return
                    num = num + 1

            elif '@AI出单' in text and text.count('出单') == 2:
                conversation: Union[Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/issuing.do'
                x = text.split()
                man_cmd = [a for a in x if '业务员' in a]
                if len(x) < 4 or len(x) > 5 or len(man_cmd) == 0 or (':' not in man_cmd[0] and '：' not in man_cmd[0]):
                    await conversation.say('@' + msg.talker().name + " 未识别到指令,请核实后重新发送!")
                    return
                salesman = man_cmd[0].split(':')[1] if ':' in man_cmd[0] else man_cmd[0].split('：')[1]
                car_licence = [a for a in x if '出单' not in a and '@' not in a and '业务员' not in a]
                if len(car_licence) == 0 or not_car_number(license_plate, car_licence[0]):
                    await conversation.say('@' + msg.talker().name + " 未识别到车辆信息,请核对信息!")
                    return
                car_licence = car_licence[0]
                await conversation.say('@' + msg.talker().name + " 收到出单指令,数据处理中请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'operator': "3",
                        'cmdName': text,
                        'salesman': salesman,
                        'licenseId': car_licence,
                        'appKey': "X08ASKYS",
                        'nickname': msg.talker().name
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                except:
                    await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                    return
                res_dict = json.loads(response.text)
                if res_dict['errorCode'] != "":
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
                    return
                num = 0
                second = sleep_time(0, 0, 5)
                while True:
                    time.sleep(second)
                    url = ip + 'api/RobotApi/pullPolicy.do'
                    multipart_encoder = MultipartEncoder(
                        fields={
                            'uuid': res_dict['data'],
                            'appKey': "X08ASKYS"
                        },
                        boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                    )
                    headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                    try:
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                    except:
                        if num == 6:
                            await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if response_dict['errorCode'] != "":
                        await conversation.say('@' + msg.talker().name + response_dict['errorMsg'])
                        return
                    if num == 6:
                        await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                        return
                    elif response_dict['success']:
                        await conversation.say('@' + msg.talker().name + ' 已完成出单!')
                        qr = FileBox.from_base64(open("qr.txt", "rb").read(), "qr.jpg")
                        await conversation.say(qr)
                        file_box = FileBox.from_base64(
                            str.encode(str(response_dict['data']).split(',')[1]),
                            name='qr.jpg')
                        await conversation.say(file_box)
                        return
                    num = num + 1

            elif '@AI出单' in text and '录单' in text:
                conversation: Union[Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/policy.do'
                x = text.split()
                man_cmd = [a for a in x if '业务员' in a]
                phone_cmd = [a for a in x if '手机' in a]
                insurance_cmd = [a for a in x if '险种' in a]
                if len(x) != 8 or len(man_cmd) == 0 or len(phone_cmd) == 0 \
                    or (':' not in man_cmd[0] and '：' not in man_cmd[0]) \
                    or (':' not in phone_cmd[0] and '：' not in phone_cmd[0]):
                    await conversation.say('@' + msg.talker().name + " 未识别到指令,请核实后重新发送!")
                    return
                salesman = man_cmd[0].split(':')[1] if ':' in man_cmd[0] else man_cmd[0].split('：')[1]
                phone = phone_cmd[0].split(':')[1] if ':' in phone_cmd[0] else phone_cmd[0].split('：')[1]
                insurance = insurance_cmd[0].split(':')[1] if ':' in insurance_cmd[0] else insurance_cmd[0].split('：')[
                    1]
                if '基本' in insurance:
                    if len(x) == 5:
                        if len([a for a in x if '-商业' in a]) != 0:
                            jqInsurance = 'true'
                            csInsurance = 'false'
                            szInsurance = None
                            driver = None
                            passenger = None
                            accident = None
                        else:
                            jqInsurance = 'false' if [a for a in x if '-交强' in a] else 'true'
                            if len([a for a in x if '-车损' in a]) != 0:
                                csInsurance = 'false'
                            elif len([a for a in x if '车损' in a and '-' not in a]) != 0:
                                csInsurance = get_number(a for a in x if '车损' in a)
                            else:
                                csInsurance = 'true'
                            szInsurance = '100' if len([a for a in x if '三者' in a]) == 0 else get_number(
                                str([a for a in x if '三者' in a]))
                            driver = '1' if len([a for a in x if '司机' in a]) == 0 else get_number(
                                str([a for a in x if '司机' in a]))
                            passenger = '1' if len([a for a in x if '乘客' in a]) == 0 else get_number(
                                str([a for a in x if '乘客' in a]))
                            accident = None if len([a for a in x if '意外' in a]) == 0 else get_number(
                                str([a for a in x if '意外' in a]))
                    elif len(x) == 7:
                        jqInsurance = 'true'
                        csInsurance = 'true'
                        szInsurance = get_number(str([a for a in x if '三者' in a]))
                        driver = get_number(str([a for a in x if '司机' in a]))
                        passenger = get_number(str([a for a in x if '乘客' in a]))
                        accident = None
                    else:
                        await conversation.say('@' + msg.talker().name + " 未识别到指令，请核实后重新发送!")
                        return
                elif '进阶' in insurance:
                    if len(x) == 5:
                        if len([a for a in x if '-商业' in a]) != 0:
                            jqInsurance = 'true'
                            csInsurance = 'false'
                            szInsurance = None
                            driver = None
                            passenger = None
                            accident = None
                        else:
                            jqInsurance = 'false' if [a for a in x if '-交强' in a] else 'true'
                            if len([a for a in x if '-车损' in a]) != 0:
                                csInsurance = 'false'
                            elif len([a for a in x if '车损' in a and '-' not in a]) != 0:
                                csInsurance = get_number(a for a in x if '车损' in a)
                            else:
                                csInsurance = 'true'
                            szInsurance = '150' if len([a for a in x if '三者' in a]) == 0 else get_number(
                                str([a for a in x if '三者' in a]))
                            driver = '5' if len([a for a in x if '司机' in a]) == 0 else get_number(
                                str([a for a in x if '司机' in a]))
                            passenger = '5' if len([a for a in x if '乘客' in a]) == 0 else get_number(
                                str([a for a in x if '乘客' in a]))
                            accident = None if len([a for a in x if '意外' in a]) == 0 else get_number(
                                str([a for a in x if '意外' in a]))
                    elif len(x) == 7:
                        jqInsurance = 'true'
                        csInsurance = 'true'
                        szInsurance = get_number(str([a for a in x if '三者' in a]))
                        driver = get_number(str([a for a in x if '司机' in a]))
                        passenger = get_number(str([a for a in x if '乘客' in a]))
                        accident = None
                    else:
                        await conversation.say('@' + msg.talker().name + " 未识别到指令，请核实后重新发送!")
                        return
                szInsurance = szInsurance[0]
                driver = driver[0]
                passenger = passenger[0]
                await conversation.say('@' + msg.talker().name + " 收到录单指令,数据处理中请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'operator': "4",
                        'cmdName': text,
                        'salesman': salesman,
                        'jqInsurance': jqInsurance,
                        'csInsurance': csInsurance,
                        'szInsurance': szInsurance,
                        'driver': driver,
                        'passenger': passenger,
                        'accident': None if accident is None else '*'.join(accident),
                        'phone': phone,
                        'appKey': "X08ASKYS",
                        'nickname': msg.talker().name
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                except:
                    await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                    return
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                    return
                await conversation.say('@' + msg.talker().name + ' 已完成录单!')
                num = 0
                second = sleep_time(0, 0, 5)
                while True:
                    time.sleep(second)
                    url = ip + 'api/RobotApi/pullPolicy.do'
                    multipart_encoder = MultipartEncoder(
                        fields={
                            'uuid': res_dict['data'],
                            'appKey': "X08ASKYS"
                        },
                        boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                    )
                    headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                    try:
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                    except:
                        if num == 6:
                            await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if response_dict['errorCode'] != "":
                        await conversation.say('@' + msg.talker().name + response_dict['errorMsg'])
                        return
                    if num == 6:
                        await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                        return
                    elif response_dict['success']:
                        try:
                            data = response_dict['data']
                            await conversation.say(
                                '@' + msg.talker().name + ' 本车客户风险等级:'
                                + data['customerRiskRating'] + '; 车系风险等级:'
                                + data['familyGrade'] + '; 无赔系数:'
                                + data['unattendGrade'] + '; 自主定价系数:'
                                + data['rateProduct'] + '。')
                            await conversation.say(
                                '@' + msg.talker().name + ' '
                                + data['ownerName'] + '，您好！您的爱车'
                                + data['plateNumber'] + '预计估价共计'
                                + data['totalPremium'] + '元，其中交强险'
                                + data['compulsoryPremium'] + '元， 商业险'
                                + data['businessPremium'] + '元。商业险明细：车损保额'
                                + [a for a in data['policyBusinessCategoryList'] if "车损" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "车损" in a['name']][0][
                                    'premium'] + '元 ；三者保额'
                                + [a for a in data['policyBusinessCategoryList'] if
                                   "三者" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "三者" in a['name']][0][
                                    'premium'] + '元 ；司机保额'
                                + [a for a in data['policyBusinessCategoryList'] if "司机" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "司机" in a['name']][0][
                                    'premium'] + '元；乘客保额'
                                + [a for a in data['policyBusinessCategoryList'] if "乘客" in a['name']][0][
                                    'amountWy'] + '万元，保费'
                                + [a for a in data['policyBusinessCategoryList'] if "乘客" in a['name']][0][
                                    'premium'] + '元 。代收车船税'
                                + data['taxPremium'] + '元。此报价仅供参考，最终价格以出单为准。')
                            file_box = FileBox.from_url(
                                data['url'],
                                name='policy.jpg')
                            await conversation.say(file_box)
                            return
                        except:
                            await conversation.say('@' + msg.talker().name + " 操作报价失败，请手动操作！")
                            return
                        return
                    num = num + 1

            elif msg_type == MessageType.MESSAGE_TYPE_IMAGE:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                logger.info('receving image file')
                image: WeImage = msg.to_image()
                hd_file_box: FileBox = await image.hd()
                url = ip + 'api/RobotApi/imgUpload.do'
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'path': '/img/robotOrder',
                        'storageServer': 'FASTDFS',
                        'file': (str(int(time.time())) + '.jpg', BytesIO(hd_file_box.stream), 'image/jpeg'),
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])

            else:
                pass

            if msg.type() == MessageType.MESSAGE_TYPE_UNSPECIFIED:
                talker = msg.talker()
                assert isinstance(talker, Contact)

        elif "21121012651@chatroom" == room_id:
            if '@AI出单' in text and '查单' in text:
                pass

            elif '@AI出单' in text and '批量出单' in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                await conversation.say('@' + msg.talker().name + " 收到指令,努力处理中请稍后!")
                url = ip_js + 'api/RobotApi/wycPolicy.do'
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'operator': msg.talker().name,
                        'cmdName': text,
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                except:
                    await conversation.say('@' + msg.talker().name + "  抱歉，连接已断开，未查询到用户数据!")
                    return
                res_dict = json.loads(response.text)
                if res_dict['errorCode'] != "":
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
                    return
                num = 0
                second = sleep_time(0, 0, 5)
                while True:
                    time.sleep(second)
                    url = ip_js + 'api/RobotApi/pullPolicy.do'
                    multipart_encoder = MultipartEncoder(
                        fields={
                            'uuid': res_dict['data'],
                            'appKey': "X08ASKYS"
                        },
                        boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                    )
                    headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                    try:
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                    except:
                        if num == 6:
                            await conversation.say('@' + msg.talker().name + " 抱歉，连接已断开，未查询到用户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if response_dict['errorCode'] != "":
                        await conversation.say('@' + msg.talker().name + response_dict['errorMsg'])
                        return
                    if num == 6:
                        await conversation.say('@' + msg.talker().name + " 抱歉，连接已断开，未查询到用户数据!")
                        return
                    elif response_dict['success']:
                        try:
                            file_box = FileBox.from_url(
                                response_dict['data'],
                                name='policy.xlsx')
                            await conversation.say(file_box)
                            await conversation.say('@' + msg.talker().name + ' 完成批量出单，请查收结果!')
                            return
                        except:
                            await conversation.say('@' + msg.talker().name + " 批量出单失败，请手动操作!")
                            return
                    num = num + 1

            elif msg_type == MessageType.MESSAGE_TYPE_IMAGE:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                logger.info('receving image file')
                image: WeImage = msg.to_image()
                hd_file_box: FileBox = await image.hd()
                url = ip_js + 'api/RobotApi/imgUpload.do'
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'contactId': contact_id,
                        'path': '/img/robotOrder',
                        'storageServer': 'FASTDFS',
                        'file': (str(int(time.time())) + '.jpg', BytesIO(hd_file_box.stream), 'image/jpeg'),
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])

            elif msg_type in [MessageType.MESSAGE_TYPE_AUDIO, MessageType.MESSAGE_TYPE_ATTACHMENT, MessageType.MESSAGE_TYPE_VIDEO]:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                logger.info('receving file:' + 'test')
                file_box = await msg.to_file_box()
                url = ip_js + 'api/RobotApi/imgUpload.do'
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': room_id,
                        'operator': "6",
                        'nickname': msg.talker().name,
                        'contactId': contact_id,
                        'path': '/img/robotOrder',
                        'storageServer': 'FASTDFS',
                        'file': (
                            str(int(time.time())) + '.xlsx' if file_box.name.endswith(
                                "xlsx") else '.xls', BytesIO(file_box.stream),
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_box.name.endswith(
                                "xlsx") else 'application/vnd.ms-excel'),
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers, timeout=30)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])

                else:
                    pass

                if msg.type() == MessageType.MESSAGE_TYPE_UNSPECIFIED:
                    talker = msg.talker()
                    assert isinstance(talker, Contact)

        else:
            pass

    async def on_login(self, contact: Contact) -> None:
        """login event

        Args:
            contact (Contact): the account logined
        """
        logger.info('Contact<%s> has logined ...', contact)
        self.login_user = contact

    async def on_friendship(self, friendship: Friendship) -> None:
        """when receive a new friendship application, or accept a new friendship

        Args:
            friendship (Friendship): contains the status and friendship info,
                eg: hello text, friend contact object
        """
        MAX_ROOM_MEMBER_COUNT = 500
        # 1. receive a new friendship from someone
        if friendship.type() == FriendshipType.FRIENDSHIP_TYPE_RECEIVE:
            hello_text: str = friendship.hello()

            # accept friendship when there is a keyword in hello text
            if 'wechaty' in hello_text.lower():
                await friendship.accept()

        # 2. you have a new friend to your contact list
        elif friendship.type() == FriendshipType.FRIENDSHIP_TYPE_CONFIRM:
            # 2.1 invite the user to wechaty group
            # find the topic of room which contains Wechaty keyword
            wechaty_rooms: List[Room] = await self.Room.find_all('Wechaty')

            # 2.2 find the suitable room
            for wechaty_room in wechaty_rooms:
                members: List[Contact] = await wechaty_room.member_list()
                if len(members) < MAX_ROOM_MEMBER_COUNT:
                    contact: Contact = friendship.contact()
                    await wechaty_room.add(contact)
                    break

    async def on_room_join(self, room: Room, invitees: List[Contact],
                           inviter: Contact, date: datetime) -> None:
        """on_room_join when there are new contacts to the room

        Args:
                room (Room): the room instance
                invitees (List[Contact]): the new contacts to the room
                inviter (Contact): the inviter who share qrcode or manual invite someone
                date (datetime): the datetime to join the room
        """
        # 1. say something to welcome the new arrivals
        names: List[str] = []
        for invitee in invitees:
            await invitee.ready()
            names.append(invitee.name)

        await room.say(f'welcome {",".join(names)} to the wechaty group !')


license_plate = "([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]" \
                "{1}(([A-HJ-Z]{1}[A-HJ-NP-Z0-9]{5})|([A-HJ-Z]{1}(([DF]{1}[A-HJ-NP-Z0-9]{1}[0-9]{4})|([0-9]{5}[DF]" \
                "{1})))|([A-HJ-Z]{1}[A-D0-9]{1}[0-9]{3}警)))|([0-9]{6}使)|((([沪粤川云桂鄂陕蒙藏黑辽渝]{1}A)|鲁B|闽D|蒙E|蒙H)" \
                "[0-9]{4}领)|(WJ[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼·•]{1}[0-9]{4}[TDSHBXJ0-9]{1})" \
                "|([VKHBSLJNGCE]{1}[A-DJ-PR-TVY]{1}[0-9]{5})"

frame = "[A-HJ-NPR-Z\d]{17}$"


def create_qr(test):
    imgdata = base64.b64decode(test)
    file = open('qr.jpg', 'wb')
    file.write(imgdata)
    file.close()


def sleep_time(time_hour, time_min, time_second):
    return time_hour * 3600 + time_min * 60 + time_second


def not_car_number(pattern, string):
    if re.findall(pattern, string):
        return False
    else:
        return True


def get_number(string):
    return re.findall(r"\d+\.?\d*", string)


asyncio.run(main())
