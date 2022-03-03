import sys
from os.path import abspath, dirname, join

from typing import Dict, List, MutableMapping, Optional, Tuple
import pytest
from wechaty_grpc.wechaty.puppet import MessageType
from wechaty_puppet.puppet import Puppet
from wechaty_puppet.schemas.message import MessageQueryFilter
from wechaty_puppet.schemas.room import RoomQueryFilter
from wechaty_puppet.schemas.types import (
    MessagePayload,
    RoomPayload,
    ContactPayload,
    RoomMemberPayload,
)
from wechaty_puppet.schemas.puppet import PuppetOptions

WORKSPACE = dirname(dirname(abspath(__file__)))
SCRIPT_DIR = join(WORKSPACE, "src")
sys.path.append(SCRIPT_DIR)

from wechaty.wechaty import Wechaty, WechatyOptions  # noqa


class FakePuppet(Puppet):
    """A fake puppet implementation that can be used for tests"""

    def __init__(self, options: PuppetOptions, name: str = "fake_puppet"):
        super().__init__(options, name=name)

        self.fake_messages: MutableMapping[str, MessagePayload] = {}
        self.fake_rooms: MutableMapping[str, RoomPayload] = {}
        self.fake_contacts: MutableMapping[str, ContactPayload] = {}
        self.fake_room_members: Dict[Tuple[str, str], RoomMemberPayload] = {}

    def add_message(self, payload: MessagePayload) -> None:
        """Manually add a message that can be looked up later"""
        print(payload.id)
        self.fake_messages[payload.id] = payload

    def add_room(self, payload: RoomPayload) -> None:
        """Manually add a room that can be looked up later"""
        self.fake_rooms[payload.id] = payload

    def add_contact(self, payload: ContactPayload) -> None:
        """Manually add a contact that can be looked up later"""
        self.fake_contacts[payload.id] = payload

    def add_room_member(self, room_id: str, payload: RoomMemberPayload) -> None:
        """Manually add a room member that can be looked up later"""
        self.fake_room_members[(room_id, payload.id)] = payload

    async def message_search(self, query: Optional[MessageQueryFilter] = None) -> List[str]:
        return [query.id]

    async def room_search(self, query: Optional[MessageQueryFilter] = None) -> List[str]:
        return self.fake_rooms[query.id] if query else self.fake_rooms.keys()

    async def room_members(self, room_id: str) -> List[str]:
        return [
            room_member
            for (key, room_member) in self.fake_room_members.items()
            if key[0] == room_id
        ]

    async def message_payload(self, message_id: str) -> MessagePayload:
        print(f"Finding {message_id}")
        return self.fake_messages[message_id]

    async def room_member_payload(
        self, room_id: str, contact_id: str
    ) -> Optional[RoomMemberPayload]:
        return self.fake_room_members.get((room_id, contact_id))

    async def room_payload(self, room_id: str) -> RoomPayload:
        return self.fake_rooms[room_id]

    async def contact_payload(self, contact_id: str) -> ContactPayload:
        return self.fake_contacts[contact_id]


@pytest.fixture
async def test_bot() -> Wechaty:
    """Initialize a Wechaty instance and return it"""
    puppet = FakePuppet(options=PuppetOptions())
    puppet.add_contact(ContactPayload("wechaty_user", name="Wechaty User"))
    puppet.add_contact(ContactPayload("fake_user", name="Fake User"))
    puppet.add_contact(ContactPayload("test_user", name="Test User"))
    puppet.add_room(
        RoomPayload(
            id="test_room",
            topic="test_room",
            owner_id="wechaty_user",
            member_ids=["wechaty_user", "fake_user", "test_user"],
        )
    )
    puppet.add_room(
        RoomPayload(
            id="fake_room",
            topic="fake_room",
            owner_id="wechaty_user",
            member_ids=["wechaty_user", "fake_user", "test_user"],
        )
    )
    puppet.add_room_member("fake_room", RoomMemberPayload("wechaty_user"))
    puppet.add_room_member("fake_room", RoomMemberPayload("fake_user", room_alias="Fake Alias"))
    puppet.add_room_member("fake_room", RoomMemberPayload("test_user"))
    puppet.add_message(
        MessagePayload("no_mention", text="foo bar asd", type=MessageType.MESSAGE_TYPE_TEXT)
    )
    puppet.add_message(
        MessagePayload(
            "room_no_mention",
            text="beep",
            room_id="fake_room",
            type=MessageType.MESSAGE_TYPE_TEXT,
        )
    )
    puppet.add_message(
        MessagePayload(
            "room_with_mentions",
            text="@Wechaty User @Test User test message asd",
            room_id="fake_room",
            type=MessageType.MESSAGE_TYPE_TEXT,
            mention_ids=["wechaty_user", "test_user"],
        )
    )
    puppet.add_message(
        MessagePayload(
            "room_with_mentions_and_alias",
            text="123123 @Wechaty User @Test User @Fake Alias kkasd",
            room_id="fake_room",
            type=MessageType.MESSAGE_TYPE_TEXT,
            mention_ids=["wechaty_user", "test_user", "fake_user"],
        )
    )
    puppet.add_message(
        MessagePayload(
            "room_with_mentions_and_alias_mismatched",
            text="123123@Wechaty User @Test User @Fake User beep",
            room_id="fake_room",
            type=MessageType.MESSAGE_TYPE_TEXT,
            mention_ids=["wechaty_user", "test_user", "fake_user"],
        )
    )
    puppet.add_message(
        MessagePayload(
            "room_with_text_mentions",
            text="@Wechaty User @Test User @Fake Alias beep!!",
            room_id="fake_room",
            type=MessageType.MESSAGE_TYPE_TEXT,
        )
    )

    bot = Wechaty(WechatyOptions(puppet=puppet))
    await bot.init_puppet()
    return bot
