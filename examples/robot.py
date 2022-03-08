"""example code for ding-dong-bot with oop style"""
import asyncio
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
    Image,
    Friendship,
    FriendshipType,
    EventReadyPayload
)
from wechaty_puppet import get_logger

logger = get_logger(__name__)

license_plate = "([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]" \
                "{1}(([A-HJ-Z]{1}[A-HJ-NP-Z0-9]{5})|([A-HJ-Z]{1}(([DF]{1}[A-HJ-NP-Z0-9]{1}[0-9]{4})|([0-9]{5}[DF]" \
                "{1})))|([A-HJ-Z]{1}[A-D0-9]{1}[0-9]{3}警)))|([0-9]{6}使)|((([沪粤川云桂鄂陕蒙藏黑辽渝]{1}A)|鲁B|闽D|蒙E|蒙H)" \
                "[0-9]{4}领)|(WJ[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼·•]{1}[0-9]{4}[TDSHBXJ0-9]{1})" \
                "|([VKHBSLJNGCE]{1}[A-DJ-PR-TVY]{1}[0-9]{5})"

frame = "[A-HJ-NPR-Z\d]{17}$"

combo = {'基本款': '交强险 车损险 三者险100万 司机1万 乘客1万'
    , '进阶款': '交强险 车损险 三者险100万 司机1万 乘客1万'
    , '不投保交强险': '车损险 三者险100万 司机1万 乘客1万'
    , '不投保商业险': '交强险 车损险 司机1万 乘客1万'
    , '不投保车损': '交强险 三者险100万 司机1万 乘客1万'
    , '不投保司机': '交强险 车损险 三者险100万 乘客1万'
    , '不投保乘客': '交强险 车损险 三者险100万 司机1万'
    , '修改三者保额': '交强险 车损险 三者险300万 司机1万 乘客1万'
    , '修改司机保额': '交强险 车损险 三者险100万 司机5万 乘客1万'
    , '修改乘客保额': '交强险 车损险 三者险100万 司机1万 乘客5万'
    , '修改车损险绝对免赔额': '交强险 车损险2000万 三者险100万 司机1万 乘客1万'
    , '添加意外险': '交强险 车损险 三者险100万 司机1万 乘客1万 意外30,2'}


def not_car_number(pattern, string):
    if re.findall(pattern, string):
        return False
    else:
        return True


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
            if '@AI机器人' in text and '查单' not in text and '报价' not in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                await conversation.say('@' + msg.talker().name + ' 请输入指令!')

            elif '@AI机器人' in text and '查单' in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/policy.do'
                x = text.split()
                y = x.index('查单') + 1
                try:
                    z = x[y]
                except:
                    z = None
                if z is None or len(z) == 0 or not_car_number(license_plate, z):
                    await conversation.say('@' + msg.talker().name + " 未识别到车辆信息,请核对信息!")
                    return
                await conversation.say('@' + msg.talker().name + " 收到查单指令,识别到车辆信息,数据处理中请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': roomId,
                        'contactId': contactId,
                        'operator': "1",
                        'cmdName': text,
                        'licenseId': z,
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                try:
                    response = requests.get(url, data=multipart_encoder, headers=headers, timeout=5)
                except:
                    await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                    return
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + " 未查询到用户数据!")
                    return
                elif res_dict['success']:
                    await conversation.say('@' + msg.talker().name + ' 请查看' + z + '的电子保单文件!')
                    res_dict = json.loads(response.text)
                    file_box = FileBox.from_url(
                        res_dict['url'],
                        name=res_dict['fileName'])
                    await conversation.say(file_box)

            elif '@AI机器人' in text and '报价' in text:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                url = ip + 'api/RobotApi/declaration.do'
                x = text.split()
                y = x.index('险种') + 1
                try:
                    insurance = x[y]
                    cmd = " ".join([b for b in x if y < x.index(b)])
                except:
                    insurance = None
                    cmd = None

                if insurance is None or len(insurance) == 0 or cmd != combo[x[y]]:
                    await conversation.say('@' + msg.talker().name + " 未识别到指令,请重新核实后发送!")
                    return

                await conversation.say('@' + msg.talker().name + " 收到报价指令,努力处理中,请稍后!")
                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': roomId,
                        'contactId': contactId,
                        'operator': "2",
                        'cmdName': text,
                        'appKey': "X08ASKYS"
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers, timeout=5)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + " 未查询到客户数据!")
                    return
                elif res_dict['success']:
                    await conversation.say('@' + msg.talker().name + ' 请查看' + insurance + '的电子保单文件!')
                    res_dict = json.loads(response.text)
                    file_box = FileBox.from_url(
                        res_dict['url'],
                        name=res_dict['fileName'])
                    await conversation.say(file_box)

            elif msg_type == MessageType.MESSAGE_TYPE_IMAGE:
                conversation: Union[
                    Room, Contact] = from_contact if room is None else room
                await conversation.ready()
                logger.info('receving image file')
                image: Image = msg.to_image()
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


async def main() -> None:
    """doc"""
    bot = MyBot()
    os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = '28cf22af-5fa6-4912-9dba-1e4c034de38f'
    os.environ['WECHATY_PUPPET'] = 'wechaty-puppet-padlocal'
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '172.30.80.199:8788'
    await bot.start()


asyncio.run(main())
