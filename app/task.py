import json
import random
from itertools import groupby

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from requests_toolbelt import MultipartEncoder
from wechaty import Wechaty
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import FileBox, get_logger

logger = get_logger(__name__)

# 25398111924@chatroom
ip = ''
# 21121012651@chatroom
ip_js = ''
appKey = "Q7MOS4NQ"


class Task(WechatyPlugin):

    @property
    def name(self) -> str:
        return '定时任务'

    async def choice(self):
        url = ip + 'api/RobotApi/batchPullPolicy.do'
        multipart_encoder = MultipartEncoder(
            fields={
                'appKey': appKey
            },
            boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
        )
        headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
        try:
            response = requests.post(url, data=multipart_encoder, headers=headers, timeout=10)
        except:
            return
        obj = json.loads(response.text)
        if len(obj) == 0:
            return
        room_ret = list()
        for _, group in groupby(obj, lambda x: x.get('roomId')):
            room_ret.append(list(group))
        for i in room_ret:
            await self.choice_room(i)

    async def choice_room(self, obj):
        ret = list()
        for _, group in groupby(obj, lambda x: x.get('operator')):
            ret.append(list(group))
        for i in ret:
            if i[0]['operator'] == 1:
                pass
            elif i[0]['operator'] == 2:
                pass
            elif i[0]['operator'] == 3:
                pass
            elif i[0]['operator'] == 4:
                pass
            elif i[0]['operator'] == 5:
                await self.chu_dan(i)
            elif i[0]['operator'] == 6:
                await self.cha_dan(i)

    async def chu_dan(self, obj):
        room_id = obj[0]['roomId']
        room = self.bot.Room.load(room_id)
        await room.ready()
        for i in obj:
            if not i['success'] and i['errorCode'] != "":
                await room.say('@' + i['nickname'] + ' ' + i['errorMsg'])
                return
            else:
                await room.say('@' + i['nickname'] + ' 完成批量出单，请查收结果!')
                file_box = FileBox.from_url(
                    i['data'],
                    name='机器人出单反馈.xlsx' if str(i['data']).endswith("xlsx") else '机器人出单反馈.xls')
                await room.say(file_box)

    async def cha_dan(self, obj):
        room_id = obj[0]['roomId']
        room = self.bot.Room.load(room_id)
        await room.ready()
        for i in obj:
            if not i['success'] and i['errorCode'] != "":
                await room.say('@' + i['nickname'] + ' ' + i['errorMsg'])
                return
            else:
                data = i['data']
                await room.say('@' + i['nickname'] + ' 完成批量查单，请查收结果!')
                file_box = FileBox.from_url(
                    data['excel'],
                    name='机器人查单反馈.xlsx' if str(data['excel']).endswith("xlsx") else '机器人查单反馈.xls')
                await room.say(file_box)
                await room.say('@' + i['nickname'] + ' 下载地址：' + data['zip'])

    async def init_plugin(self, wechaty: Wechaty):
        await super().init_plugin(wechaty)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.choice, trigger='cron', second='*/5', max_instances=10)
        scheduler.start()
