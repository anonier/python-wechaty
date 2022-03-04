"""example code for ding-dong-bot with oop style"""
import asyncio
import json
import os
import random
import time
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Union

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from wechaty_puppet import get_logger

from src.wechaty import (
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

logger = get_logger(__name__)


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
        file_box: Optional[FileBox] = None

        # 主机
        ip = 'http://192.168.1.196/'

        if '@壹加壹' in text and '保单' not in text:
            conversation: Union[
                Room, Contact] = from_contact if room is None else room
            await conversation.ready()
            # for num in range(10,20):
            await conversation.say('@' + msg.talker().name + '哎呀 别动')
            # file_box = FileBox.from_url(
            #     'http://img.v39pay.com/img/offlineFile/aa.pdf',
            #     name='ding-dong.pdf')
            # await conversation.say(file_box)

        elif '@壹加壹' in text and '保单' in text:
            conversation: Union[
                Room, Contact] = from_contact if room is None else room
            await conversation.ready()
            await conversation.say('正在查询保单信息,请稍后')
            url = ip + 'api/RobotApi/declaration.do'
            if '车牌号' in text:
                x = text.split()
                y = x.index('车牌号') + 1

                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': roomId,
                        'contactId': contactId,
                        'operator': "1",
                        'cmdName': text,
                        'licenseId': x[y]
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
                await conversation.say('@' + msg.talker().name + '获取保单成功')
            elif '车架号' in text:
                x = text.split()
                y = x.index('车架号') + 1

                multipart_encoder = MultipartEncoder(
                    fields={
                        'roomId': roomId,
                        'contactId': contactId,
                        'operator': "1",
                        'cmdName': text,
                        'licenseId': x[y]
                    },
                    boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
                )
                headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
                response = requests.post(url, data=multipart_encoder, headers=headers)
                res_dict = json.loads(response.text)
                if not res_dict['success']:
                    await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
                await conversation.say('@' + msg.talker().name + '获取保单成功')
        elif msg_type == MessageType.MESSAGE_TYPE_IMAGE:
            conversation: Union[
                Room, Contact] = from_contact if room is None else room
            await conversation.ready()
            logger.info('receving image file')
            # file_box: FileBox = await msg.to_file_box()
            image: Image = msg.to_image()
            hd_file_box: FileBox = await image.hd()

            url = ip + 'api/RobotApi/imgUpload.do'
            multipart_encoder = MultipartEncoder(
                fields={
                    'roomId': roomId,
                    'contactId': contactId,
                    'path': '/img/robotOrder',
                    'storageServer': 'FASTDFS',
                    'file': (str(int(time.time())) + '.jpg', BytesIO(hd_file_box.stream), 'image/jpeg')
                },
                boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
            )
            headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
            response = requests.post(url, data=multipart_encoder, headers=headers)
            res_dict = json.loads(response.text)
            if not res_dict['success']:
                await conversation.say('@' + msg.talker().name + res_dict['errorMsg'])
            await msg.say(hd_file_box)
        # 保存到本地
        # await hd_file_box.to_file('/logs/robot/hd-image.jpg', overwrite=True)
        # thumbnail_file_box: FileBox = await image.thumbnail()
        # await thumbnail_file_box.to_file('/logs/robot/thumbnail-image.jpg', overwrite=True)
        # artwork_file_box: FileBox = await image.artwork()
        # await artwork_file_box.to_file('/logs/robot/artwork-image.jpg', overwrite=True)
        # # reply the image

        elif msg_type in [MessageType.MESSAGE_TYPE_AUDIO, MessageType.MESSAGE_TYPE_ATTACHMENT,
                          MessageType.MESSAGE_TYPE_VIDEO]:
            logger.info('receving file ...')
            file_box = await msg.to_file_box()
            if file_box:
                await file_box.to_file(file_box.name)

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
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '172.18.39.141:8788'
    await bot.start()


asyncio.run(main())
