import json
import random

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from requests_toolbelt import MultipartEncoder
from wechaty import Wechaty
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import FileBox

ip = 'http://192.168.1.111/'


class Task(WechatyPlugin):

    @property
    def name(self) -> str:
        return '定时任务'

    async def cmd(self):
        room_id = '25398111924@chatroom'
        room = self.bot.Room.load(room_id)
        url = ip + 'api/RobotApi/pullPolicy.do'
        multipart_encoder = MultipartEncoder(
            fields={
                'roomId': room_id,
                'operator': "4",
                'appKey': "X08ASKYS"
            },
            boundary='-----------------------------' + str(random.randint(1e28, 1e29 - 1))
        )
        headers = {'Referer': url, 'Content-Type': multipart_encoder.content_type}
        # await room.ready()
        # try:
        #     response = requests.post(url, data=multipart_encoder, headers=headers, timeout=10)
        # except:
        #     await room.say('@' + '' + " 未查询到客户数据!")
        #     return
        # x = json.loads(response.text)
        # res_dict = json.loads(x['data'])
        # for key, value in json.loads(res_dict['data']).items():
        #     file_box = FileBox.from_url(
        #         value,
        #         name=key)
        #     await room.say(file_box)

    async def init_plugin(self, wechaty: Wechaty):
        await super().init_plugin(wechaty)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.cmd(), trigger='cron', second='*/10')
        scheduler.start()
