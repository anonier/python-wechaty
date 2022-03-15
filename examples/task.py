from apscheduler.schedulers.asyncio import AsyncIOScheduler
from wechaty import Wechaty
from wechaty.plugin import WechatyPlugin


class task(WechatyPlugin):
    @property
    def name(self) -> str:
        return '定时任务'

    async def tick(self):
        roomid = '25398111924@chatroom'
        room = self.bot.Room.load(roomid)
        await room.ready()
        await room.say("摩西摩西")

    async def init_plugin(self, wechaty: Wechaty):
        await super().init_plugin(wechaty)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.tick, 'cron', minute=0, second=0)
        scheduler.start()
