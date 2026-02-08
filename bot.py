import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import discord

CONFIG_PATH = Path("config.json")
DATA_DIR = Path("data")
INVITE_DATA_PATH = DATA_DIR / "invites.json"


@dataclass
class BotConfig:
    token: str
    guild_id: int
    log_channel_id: int
    message_template: str


class InviteTracker:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._invites: dict[int, dict[str, int]] = {}
        self._counts: dict[int, int] = {}

    async def load(self) -> None:
        if not INVITE_DATA_PATH.exists():
            return
        data = json.loads(INVITE_DATA_PATH.read_text(encoding="utf-8"))
        self._counts = {int(k): int(v) for k, v in data.get("counts", {}).items()}

    async def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "counts": {str(k): v for k, v in self._counts.items()},
        }
        INVITE_DATA_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    async def sync_guild_invites(self, guild: discord.Guild) -> None:
        invites = await guild.invites()
        async with self._lock:
            self._invites[guild.id] = {invite.code: invite.uses or 0 for invite in invites}

    async def detect_used_invite(
        self, guild: discord.Guild
    ) -> tuple[discord.Invite | None, int | None]:
        invites = await guild.invites()
        async with self._lock:
            previous = self._invites.get(guild.id, {})
            for invite in invites:
                previous_uses = previous.get(invite.code, 0)
                current_uses = invite.uses or 0
                if current_uses > previous_uses:
                    self._invites[guild.id] = {
                        i.code: i.uses or 0 for i in invites
                    }
                    return invite, current_uses
            self._invites[guild.id] = {i.code: i.uses or 0 for i in invites}
        return None, None

    async def increment_inviter(self, inviter_id: int) -> int:
        async with self._lock:
            self._counts[inviter_id] = self._counts.get(inviter_id, 0) + 1
            count = self._counts[inviter_id]
        await self.save()
        return count


class InviteBot(discord.Client):
    def __init__(self, config: BotConfig, **options: object) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.invites = True
        super().__init__(intents=intents, **options)
        self.config = config
        self.tracker = InviteTracker()

    async def setup_hook(self) -> None:
        await self.tracker.load()

    async def on_ready(self) -> None:
        guild = self.get_guild(self.config.guild_id)
        if guild is None:
            return
        await self.tracker.sync_guild_invites(guild)
        print(f"Conectado como {self.user} em {guild.name}")

    async def on_invite_create(self, invite: discord.Invite) -> None:
        if invite.guild and invite.guild.id == self.config.guild_id:
            await self.tracker.sync_guild_invites(invite.guild)

    async def on_invite_delete(self, invite: discord.Invite) -> None:
        if invite.guild and invite.guild.id == self.config.guild_id:
            await self.tracker.sync_guild_invites(invite.guild)

    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id != self.config.guild_id:
            return

        invite, _ = await self.tracker.detect_used_invite(member.guild)
        if invite is None or invite.inviter is None:
            return

        count = await self.tracker.increment_inviter(invite.inviter.id)
        channel = member.guild.get_channel(self.config.log_channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            return

        message = self.config.message_template.format(
            member=member.mention,
            inviter=invite.inviter.mention,
            count=count,
        )
        await channel.send(message)


def load_config() -> BotConfig:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "Arquivo config.json não encontrado. Copie config.example.json e configure."
        )
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return BotConfig(
        token=data["token"],
        guild_id=int(data["guild_id"]),
        log_channel_id=int(data["log_channel_id"]),
        message_template=data.get(
            "message_template",
            "{member} FOI CONVIDADO POR {inviter} E AGORA TEM {count} invites.",
        ),
    )


def main() -> None:
    config = load_config()
    client = InviteBot(config)
    client.run(config.token)


if __name__ == "__main__":
    main()
