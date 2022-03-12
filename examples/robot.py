"""example code for ding-dong-bot with oop style"""
import asyncio
import base64
import json
import os
import random
import re
import time
import flask_ctr as ctr
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Union

import cv2
import numpy as np
import requests
from PIL import ImageFont, Image, ImageDraw
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

logger = get_logger(__name__)


async def main() -> None:
    """doc"""
    bot = MyBot()
    os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = '28cf22af-5fa6-4912-9dba-1e4c034de38f'
    os.environ['WECHATY_PUPPET'] = 'wechaty-puppet-padlocal'
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '192.168.1.124:8788'
    await bot.start()


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

    # pylint: disable=R0912,R0914,R0915
    async def on_message(self, msg: Message) -> None:
        """
        listen for message event
        """
        from_contact: Contact = msg.talker()
        contactId = from_contact.contact_id
        text: str = msg.text()
        room: Optional[Room] = msg.room()
        roomId = room.room_id
        msg_type: MessageType = msg.type()
        # file_box: Optional[FileBox] = None

        # 主机
        ip = 'http://192.168.1.196/'

        if room.room_id == '25398111924@chatroom':
            if '@AI出单' in text and '查单' not in text and '报价' not in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                await conversation.say('@' + msg.talker().name + ' 未识别到指令,请核实后重新发送!')

            elif '@AI出单' in text and '查单' in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/policy.do'
                x = text.split()
                y = x.index('查单') + 1
                try:
                    insurance = x[y]
                except:
                    insurance = None
                if insurance is None or len(insurance) == 0 or not_car_number(license_plate, insurance):
                    await conversation.say('@' + msg.talker().name + " 未识别到车辆信息,请核对信息!")
                    return
                await conversation.say('@' + msg.talker().name + " 收到查单指令,识别到车辆信息,数据处理中请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': roomId,
                        'contactId': contactId,
                        'operator': "1",
                        'cmdName': text,
                        'licenseId': insurance,
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.post(url, data=multipart_encoder, headers=headers, timeout=10)
                except:
                    await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                    return
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                    return
                num = 0
                second = sleep_time(0, 0, 3)
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
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=10)
                    except:
                        if num == 3:
                            await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if not response_dict['success']:
                        if num == 3:
                            await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                            return
                    elif response_dict['success']:
                        await conversation.say('@' + msg.talker().name + ' 请查看' + insurance + '的电子保单文件!')
                        for key, value in response_dict['data'].items():
                            file_box = FileBox.from_url(
                                value,
                                name=key)
                            await conversation.say(file_box)
                        return
                    num = num + 1

            elif '@AI出单' in text and '报价' in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/declaration.do'
                x = text.split()
                y = x.index('险种') + 1
                try:
                    insurance = x[y]
                except:
                    insurance = None
                if insurance is None or len(insurance) == 0:
                    await conversation.say('@' + msg.talker().name + " 未识别到保险套餐,请核实后重新发送!")
                    return
                if len(x) <= 3:
                    insurance = combo[insurance]
                    # try:
                    #     cmd = " ".join([b for b in x if y < x.index(b)])
                    # except:
                    #     cmd = None
                    # if cmd is None or cmd != combo[x[y]]:
                    #     await conversation.say('@' + msg.talker().name + " 未识别到指令,请重新核实后发送!")
                    #     return
                    # jqInsurance = 'true'
                    # csInsurance = 'true'
                    # passenger = '1'
                    # if insurance == '基本款':
                    #     szInsurance = '100'
                    #     driver = '1'
                    # elif insurance == '进阶款':
                    #     szInsurance = '150'
                    #     driver = '5'
                insurance = combo[insurance + ' ' + x[y + 1]]
                if '交强险' in insurance:
                    jqInsurance = 'true'
                else:
                    jqInsurance = 'false'
                if '车损险' in insurance:
                    csInsurance = 'true'
                elif '车损险2000' in insurance:
                    csInsurance = '2000'
                else:
                    csInsurance = 'false'
                if '三者险100万' in insurance:
                    szInsurance = '100'
                elif '三者险150万' in insurance:
                    szInsurance = '150'
                if '司机1万' in insurance:
                    driver = '1'
                elif '司机5万' in insurance:
                    driver = '5'
                if '乘客1万' in insurance:
                    passenger = '1'
                elif '乘客5万' in insurance:
                    passenger = '5'
                if '意外30*2' in insurance:
                    accident = '30 * 2'
                else:
                    accident = None
                await conversation.say('@' + msg.talker().name + " 收到报价指令,努力处理中,请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': roomId,
                        'contactId': contactId,
                        'operator': "2",
                        'cmdName': text,
                        'appKey': "X08ASKYS",
                        'jqInsurance': jqInsurance,
                        'csInsurance': csInsurance,
                        'szInsurance': szInsurance,
                        'driver': driver,
                        'passenger': passenger,
                        'accident': accident
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers, timeout=10)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                    return
                num = 0
                second = sleep_time(0, 0, 3)
                while True:
                    time.sleep(second)
                    url = ip + 'robot/query/policy'
                    multipart_encoder = MultipartEncoder(
                        fields={
                            'uuid': res_dict['data'],
                            'appKey': "X08ASKYS"
                        },
                        boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                    )
                    headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                    try:
                        response = requests.post(url, data=multipart_encoder, headers=headers, timeout=10)
                    except:
                        if num == 3:
                            await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                            return
                    response_dict = json.loads(response.text)
                    if not response_dict['success']:
                        if num == 3:
                            await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                            return
                    elif response_dict['success']:
                        await conversation.say('@' + msg.talker().name + ' 请查看' + insurance + '的电子保单文件!')
                        create_pic(response_dict['success'], response_dict['success'], response_dict['success'])
                        file_box = FileBox.from_file(
                            'img_cv.jpg',
                            name='img_cv.jpg')
                        await conversation.say(file_box)
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
                        'roomId': roomId,
                        'contactId': contactId,
                        'path': '/img/robotOrder',
                        'storageServer': 'FASTDFS',
                        'file': (str(int(time.time())) + '.jpg', BytesIO(hd_file_box.stream), 'image/jpeg'),
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])

            # 保存到本地
            # await hd_file_box.to_file('/logs/robot/hd-image.jpg', overwrite=True)
            # thumbnail_file_box: FileBox = await image.thumbnail()
            # await thumbnail_file_box.to_file('/logs/robot/thumbnail-image.jpg', overwrite=True)
            # artwork_file_box: FileBox = await image.artwork()
            # await artwork_file_box.to_file('/logs/robot/artwork-image.jpg', overwrite=True)
            # # reply the image
            #
            # elif msg_type in [MessageType.MESSAGE_TYPE_AUDIO, MessageType.MESSAGE_TYPE_ATTACHMENT,
            #                   MessageType.MESSAGE_TYPE_VIDEO]:
            #     logger.info('receving file ...')
            #     file_box = await msg.to_file_box()
            #     if file_box:
            #         await file_box.to_file(file_box.name)
            #
            # elif msg_type == MessageType.MESSAGE_TYPE_MINI_PROGRAM:
            #     logger.info('receving mini-program ...')
            #     mini_program: Optional[MiniProgram] = await msg.to_mini_program()
            #     if mini_program:
            #         await msg.say(mini_program)
            #
            # elif text == 'get room members' and room:
            #     logger.info('get room members ...')
            #     room_members: List[Contact] = await room.member_list()
            #     names: List[str] = [
            #         room_member.name for room_member in room_members]
            #     await msg.say('\n'.join(names))
            #
            # elif text.startswith('remove room member:'):
            #     logger.info('remove room member:')
            #     if not room:
            #         await msg.say('this is not room zone')
            #         return
            #
            #     room_member_name = text[len('remove room member:') + 1:]
            #
            #     room_member: Optional[Contact] = await room.member(
            #         query=RoomMemberQueryFilter(name=room_member_name)
            #     )
            #     if room_member:
            #         if self.login_user and self.login_user.contact_id in room.payload.admin_ids:
            #             await room.delete(room_member)
            #         else:
            #             await msg.say('登录用户不是该群管理员...')
            #
            #     else:
            #         await msg.say(f'can not fine room member by name<{room_member_name}>')
            # elif text.startswith('get room topic'):
            #     logger.info('get room topic')
            #     if room:
            #         topic: Optional[str] = await room.topic()
            #         if topic:
            #             await msg.say(topic)
            #
            # elif text.startswith('rename room topic:'):
            #     logger.info('rename room topic ...')
            #     if room:
            #         new_topic = text[len('rename room topic:') + 1:]
            #         await msg.say(new_topic)
            # elif text.startswith('add new friend:'):
            #     logger.info('add new friendship ...')
            #     identity_info = text[len('add new friend:'):]
            #     weixin_contact: Optional[Contact] = await self.Friendship.search(weixin=identity_info)
            #     phone_contact: Optional[Contact] = await self.Friendship.search(phone=identity_info)
            #     contact: Optional[Contact] = weixin_contact or phone_contact
            #     if contact:
            #         await self.Friendship.add(contact, 'hello world ...')
            #
            # elif text.startswith('at me'):
            #     if room:
            #         talker = msg.talker()
            #         await room.say('hello', mention_ids=[talker.contact_id])
            #
            # elif text.startswith('my alias'):
            #     talker = msg.talker()
            #     alias = await talker.alias()
            #     await msg.say('your alias is:' + (alias or ''))
            #
            # elif text.startswith('set alias:'):
            #     talker = msg.talker()
            #     new_alias = text[len('set alias:'):]
            #
            #     # set your new alias
            #     alias = await talker.alias(new_alias)
            #     # get your new alias
            #     alias = await talker.alias()
            #     await msg.say('your new alias is:' + (alias or ''))
            #
            # elif text.startswith('find friends:'):
            #     friend_name: str = text[len('find friends:'):]
            #     friend = await self.Contact.find(friend_name)
            #     if friend:
            #         logger.info('find only one friend <%s>', friend)
            #
            #     friends: List[Contact] = await self.Contact.find_all(friend_name)
            #
            #     logger.info('find friend<%d>', len(friends))
            #     logger.info(friends)

            else:
                pass

            if msg.type() == MessageType.MESSAGE_TYPE_UNSPECIFIED:
                talker = msg.talker()
                assert isinstance(talker, Contact)

        elif room.room_id != '25398111924@chatroom':
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

combo = {'基本款': '交强险 车损险 三者险100万 司机1万 乘客1万'
    , '进阶款': '交强险 车损险 三者险150万 司机5万 乘客1万'
    , '基本款 -交强': '车损险 三者险100万 司机1万 乘客1万'
    , '基本款 -商业': '交强险 车损险 司机1万 乘客1万'
    , '基本款 -车损': '交强险 三者险100万 司机1万 乘客1万'
    , '基本款 -司机': '交强险 车损险 三者险100万 乘客1万'
    , '基本款 -乘客': '交强险 车损险 三者险100万 司机1万'
    , '基本款 三者300': '交强险 车损险 三者险300万 司机1万 乘客1万'
    , '基本款 司机5': '交强险 车损险 三者险100万 司机5万 乘客1万'
    , '基本款 乘客5': '交强险 车损险 三者险100万 司机1万 乘客5万'
    , '基本款 车损2000': '交强险 车损险2000 三者险100万 司机1万 乘客1万'
    , '基本款 意外30,2': '交强险 车损险 三者险100万 司机1万 乘客1万 意外30*2'
    , '基本款 意外30，2': '交强险 车损险 三者险100万 司机1万 乘客1万 意外30*2'}


def create_pic(a, b, c, d, e, f, g):
    img_cv = cv2.imread('img.jpg')
    font = ImageFont.truetype("simfang.ttf", 14)
    img_pil = Image.fromarray(img_cv)
    draw = ImageDraw.Draw(img_pil)
    draw.text((136, 84), a, font=font, fill=(0, 0, 0))
    draw.text((136, 101), b, font=font, fill=(0, 0, 0))
    img = cv2.cvtColor(np.asarray(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imwrite("img_cv.jpg", img)
    cv2.waitKey()


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


asyncio.run(main())
