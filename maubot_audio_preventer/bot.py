from typing import Type

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from mautrix.types import EventType, GenericEvent, MessageType, TextMessageEventContent

from maubot import Plugin, MessageEvent
from maubot.handlers import event

from .db import Database, UserInfo


m_voice_event = EventType.find("m.voice",
                               t_class=EventType.Class.MESSAGE)


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("text_warning_amount")
        helper.copy("kick_warning_amount")
        helper.copy("whitelist")


class MaubotAudioPreventer(Plugin):
    db: Database

    async def start(self) -> None:
        self.config.load_and_update()
        self.db = Database(self.database)
        #self.log.debug("Loaded %s from config example 2", self.config["example_2.value"])

    async def stop(self) -> None:
        pass

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    # async def handle_voice(self, evt: )

    @event.on(EventType.ROOM_MESSAGE)
    async def audio_event_handler(self, evt: MessageEvent) -> None:
        if (evt.content.msgtype != MessageType.AUDIO):
            return

        await self.client.redact(evt.room_id, evt.event_id, "Voice messages are not allowed")

        warnings = self.db.get_user(evt.sender)
        if (warnings is None):
            await evt.reply(f"""Please do not send Audio or Voice messages. This is your first warning! You have {self.config['text_warning_amount'] - 1} warnings left before you will get kicked.\n
If you then still not comply you will after {self.config['kick_warning_amount']} kicks get banned from this room. The counter is across all rooms this bot is admin in.""")
            self.db.add_user(evt.sender)
        else:
            warnings_typed: UserInfo = warnings
            text_warnings: int = getattr(warnings_typed, 'text_warnings')
            kick_warnings: int = getattr(warnings_typed, 'kick_warnings')
            if (text_warnings - 1 != self.config['text_warning_amount']):
                await evt.reply(f"Please do not send Audio or Voice messages. This is your first warning! You have {self.config['text_warning_amount'] - text_warnings - 1} left.")
                self.db.increment_text_warnings(evt.sender, text_warnings)
            elif (kick_warnings - 1 != self.config['kick_warning_amount']):
                await self.client.kick_user(evt.room_id, evt.sender, f"You exceeded your voice message warnings. This is your first kick! You have {self.config['kick_warning_amount'] - kick_warnings - 1} left.")
                self.db.increment_kick_warnings(evt.sender, text_warnings)
            else:
                await self.client.ban_user(evt.room_id, evt.sender, "You exceeded your voice message kick warnings. You are now getting banned for spam!")

    @event.on(m_voice_event)
    async def handle_m_voice_event(self, evt: GenericEvent) -> None:
        content = TextMessageEventContent(
            msgtype=MessageType.NOTICE, content="Please do not send Audio or Voice messages. This is your first warning!")
        content.set_reply(evt.event_id)
        await self.client.send_message_event(evt.room_id, EventType.ROOM_MESSAGE, content)

        await self.client.redact(evt.room_id, evt.event_id, "Voice messages are not allowed")
        warnings = self.db.get_user(evt.sender)
        if (warnings is None):
            content = TextMessageEventContent(
                msgtype=MessageType.NOTICE, content=f"Please do not send Audio or Voice messages. This is your first warning! You have {self.config['text_warning_amount'] - 1} warnings left before you will get kicked.")
            content.set_reply(evt.event_id)

            await self.client.send_message_event(evt.room_id, EventType.ROOM_MESSAGE, content)
            self.db.add_user(evt.sender)
        else:
            warnings_typed: UserInfo = warnings
            text_warnings: int = getattr(warnings_typed, 'text_warnings')
            kick_warnings: int = getattr(warnings_typed, 'kick_warnings')
            if (text_warnings - 1 != self.config['text_warning_amount']):
                content = TextMessageEventContent(
                    msgtype=MessageType.NOTICE, content=f"Please do not send Audio or Voice messages. This is your first warning! You have {self.config['text_warning_amount'] - text_warnings - 1} left.")
                content.set_reply(evt.event_id)

                await self.client.send_message_event(evt.room_id, EventType.ROOM_MESSAGE, content)
                self.db.increment_text_warnings(evt.sender, text_warnings)
            elif (kick_warnings - 1 != self.config['kick_warning_amount']):
                await self.client.kick_user(evt.room_id, evt.sender, f"You exceeded your voice message warnings. This is your first kick! You have {self.config['kick_warning_amount'] - kick_warnings - 1} left.")
                self.db.increment_kick_warnings(evt.sender, text_warnings)
            else:
                await self.client.ban_user(evt.room_id, evt.sender, "You exceeded your voice message kick warnings. You are now getting banned for spam!")
