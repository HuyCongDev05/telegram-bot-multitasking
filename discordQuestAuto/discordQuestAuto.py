import asyncio
import base64
import json
import logging
import random
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import aiohttp

_BUILD_SIG = "687579636f6e676465763035"

try:
    from . import config as quest_config
except ImportError:
    import config as quest_config

logger = logging.getLogger(__name__)

# Lấy Build Number mới nhất từ Discord (Async)
async def fetch_latest_build_number(session: aiohttp.ClientSession) -> int:
    FALLBACK = 504649
    try:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        async with session.get("https://discord.com/app", headers={"User-Agent": ua}, timeout=15) as r:
            if r.status != 200:
                return FALLBACK
            text = await r.text()

        scripts = re.findall(r'/assets/([a-f0-9]+)\.js', text)
        if not scripts:
            scripts_alt = re.findall(r'src="(/assets/[^"]+\.js)"', text)
            scripts = [s.split('/')[-1].replace('.js', '') for s in scripts_alt]

        if not scripts:
            return FALLBACK

        for asset_hash in scripts[-5:]:
            try:
                async with session.get(
                    f"https://discord.com/assets/{asset_hash}.js",
                    headers={"User-Agent": ua}, timeout=15
                ) as ar:
                    js_text = await ar.text()
                    m = re.search(r'buildNumber["\s:]+["\s]*(\d{5,7})', js_text)
                    if m:
                        return int(m.group(1))
            except Exception:
                continue
        return FALLBACK
    except Exception:
        return FALLBACK

def make_super_properties(build_number: int) -> str:
    obj = {
        "os": "Windows", "browser": "Discord Client", "release_channel": "stable",
        "client_version": "1.0.9175", "os_version": "10.0.26100", "os_arch": "x64",
        "app_arch": "x64", "system_locale": "en-US",
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36",
        "browser_version": "32.2.7", "client_build_number": build_number,
        "native_build_number": 59498, "client_event_source": None,
    }
    return base64.b64encode(json.dumps(obj).encode()).decode()

# Client API Discord (Bất đồng bộ)
class AsyncDiscordAPI:
    def __init__(self, token: str, build_number: int, session: aiohttp.ClientSession):
        self.token = token
        self.session = session
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9175 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36"
        sp = make_super_properties(build_number)
        self.session._default_headers.update({
            "Authorization": token, "Content-Type": "application/json", "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9", "User-Agent": ua, "X-Super-Properties": sp,
            "X-Discord-Locale": "en-US", "X-Discord-Timezone": "Asia/Ho_Chi_Minh",
            "Origin": "https://discord.com", "Referer": "https://discord.com/channels/@me",
        })

    async def get(self, path: str, **kwargs) -> aiohttp.ClientResponse:
        return await self.session.get(f"{quest_config.API_BASE}{path}", **kwargs)

    async def post(self, path: str, payload: Optional[dict] = None, **kwargs) -> aiohttp.ClientResponse:
        return await self.session.post(f"{quest_config.API_BASE}{path}", json=payload, **kwargs)

    async def validate_token(self) -> Optional[Dict[str, Any]]:
        try:
            async with await self.get("/users/@me") as r:
                if r.status == 200:
                    return await r.json()
                return None
        except Exception:
            return None

# Các hàm hỗ trợ Quest
def _get(d: Optional[dict], *keys):
    if d is None: return None
    for k in keys:
        if k in d: return d[k]
    return None

def get_task_config(quest: dict) -> Optional[dict]:
    return _get(quest.get("config", {}), "taskConfig", "task_config", "taskConfigV2", "task_config_v2")

def get_quest_name(quest: dict) -> str:
    cfg = quest.get("config", {})
    msgs = cfg.get("messages", {})
    name = _get(msgs, "questName", "quest_name") or _get(msgs, "gameTitle", "game_title") or cfg.get("application", {}).get("name")
    return name.strip() if name else f"Quest#{quest.get('id', '?')}"

def is_completable(quest: dict) -> bool:
    expires = _get(quest.get("config", {}), "expiresAt", "expires_at")
    if expires:
        try:
            if datetime.fromisoformat(expires.replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                return False
        except Exception: pass
    tc = get_task_config(quest)
    if not tc or "tasks" not in tc: return False
    return any(tc["tasks"].get(t) is not None for t in quest_config.SUPPORTED_TASKS)

def is_enrolled(quest: dict) -> bool:
    us = _get(quest, "userStatus", "user_status") or {}
    return bool(_get(us, "enrolledAt", "enrolled_at"))

def is_completed(quest: dict) -> bool:
    us = _get(quest, "userStatus", "user_status") or {}
    return bool(_get(us, "completedAt", "completed_at"))

def get_task_type(quest: dict) -> Optional[str]:
    tc = get_task_config(quest)
    if not tc or "tasks" not in tc: return None
    for t in quest_config.SUPPORTED_TASKS:
        if tc["tasks"].get(t) is not None: return t
    return None

def get_seconds_needed(quest: dict) -> int:
    tc = get_task_config(quest)
    tt = get_task_type(quest)
    return tc["tasks"][tt].get("target", 0) if tc and tt else 0

def get_seconds_done(quest: dict) -> float:
    tt = get_task_type(quest)
    if not tt: return 0
    us = _get(quest, "userStatus", "user_status") or {}
    return us.get("progress", {}).get(tt, {}).get("value", 0)

# Bộ tự động hoàn thành Quest (Bất đồng bộ)
class AsyncQuestAutocompleter:
    def __init__(self, api: AsyncDiscordAPI, bot=None, chat_id=None):
        self.api = api
        self.bot = bot
        self.chat_id = chat_id
        self.completed_ids = set()
        self.is_running = True

    async def log_to_bot(self, msg: str, level: str = "info"):
        datetime.now().strftime("%H:%M:%S")
        _, emoji = {
            "info":     ("[TIN]", "ℹ️"),
            "ok":       ("[ OK]", "✅"),
            "warn":     ("[CHÚ]", "⚠️"),
            "error":    ("[LỖI]", "❌"),
            "progress": ("[TĐ ]", "⏳"),
            "debug":    ("[DBG]", "🔍"),
        }.get(level, (f"[{level.upper()}]", "❓"))

        if level == "debug" and not quest_config.DEBUG:
            return

        if quest_config.LOG_PROGRESS or level != "progress":
            # bỏ qua đầu ra terminal theo yêu cầu
            if self.bot and self.chat_id:
                if level in ("ok", "warn", "error") or (level == "info" and "━━━" in msg):
                    try:
                        await self.bot.send_message(
                            chat_id=self.chat_id,
                            text=msg,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Error sending log to Telegram: {e}")

    async def fetch_quests(self) -> list:
        try:
            async with await self.api.get("/quests/@me") as r:
                if r.status == 200:
                    data = await r.json()
                    if isinstance(data, dict):
                        if data.get("quest_enrollment_blocked_until"):
                            await self.log_to_bot(f"Bị chặn nhận quest đến: {data['quest_enrollment_blocked_until']}", "warn")
                        return data.get("quests", [])
                    return data if isinstance(data, list) else []
                elif r.status == 429:
                    retry = (await r.json()).get("retry_after", 10)
                    await self.log_to_bot(f"Giới hạn tốc độ – chờ {retry}s", "warn")
                    await asyncio.sleep(retry)
                    return await self.fetch_quests()
                return []
        except Exception as e:
            await self.log_to_bot(f"Lỗi tải danh sách quest: {e}", "error")
            return []

    async def enroll_quest(self, quest: dict) -> bool:
        name = get_quest_name(quest)
        qid = quest["id"]
        for attempt in range(1, 4):
            try:
                async with await self.api.post(f"/quests/{qid}/enroll", {
                    "location": 11, "is_targeted": False, "metadata_raw": None, "metadata_sealed": None,
                    "traffic_metadata_raw": quest.get("traffic_metadata_raw"),
                    "traffic_metadata_sealed": quest.get("traffic_metadata_sealed"),
                }) as r:
                    if r.status == 429:
                        wait = (await r.json()).get("retry_after", 5) + 1
                        await asyncio.sleep(wait)
                        continue
                    if r.status in (200, 201, 204):
                        await self.log_to_bot(f"Đã nhận: {name}", "ok")
                        return True
                    await self.log_to_bot(f"Lỗi nhận \"{name}\" ({r.status})", "warn")
                    return False
            except Exception as e:
                await self.log_to_bot(f"Lỗi nhận \"{name}\": {e}", "error")
                return False
        return False

    async def auto_accept(self, quests: list) -> list:
        if not quest_config.AUTO_ACCEPT: return quests
        unaccepted = [q for q in quests if not is_enrolled(q) and not is_completed(q) and is_completable(q)]
        if not unaccepted: return quests
        await self.log_to_bot(f"Phát hiện {len(unaccepted)} quest mới – đang nhận...", "info")
        for q in unaccepted:
            await self.enroll_quest(q)
            await asyncio.sleep(3)
        return await self.fetch_quests()

    async def complete_video(self, quest: dict):
        name = get_quest_name(quest)
        qid = quest["id"]
        needed = get_seconds_needed(quest)
        done = get_seconds_done(quest)
        enrolled_at = _get(_get(quest, "userStatus", "user_status"), "enrolledAt", "enrolled_at")
        enrolled_ts = datetime.fromisoformat(enrolled_at.replace("Z", "+00:00")).timestamp() if enrolled_at else datetime.now().timestamp()

        await self.log_to_bot(f"🎬 Video: {name} ({done:.0f}/{needed}s)", "info")
        while done < needed and self.is_running:
            max_allowed = (datetime.now().timestamp() - enrolled_ts) + 10
            ts = done + 7
            if max_allowed - done >= 7:
                try:
                    async with await self.api.post(f"/quests/{qid}/video-progress", {"timestamp": min(needed, ts + random.random())}) as r:
                        if r.status == 200:
                            body = await r.json()
                            if body.get("completed_at"):
                                await self.log_to_bot(f"Xong: {name}", "ok")
                                return
                            done = min(needed, ts)
                            await self.log_to_bot(f"  {name}: {done:.0f}/{needed}s", "progress")
                        elif r.status == 429:
                            await asyncio.sleep((await r.json()).get("retry_after", 5) + 1)
                            continue
                except Exception: pass
            if ts >= needed: break
            await asyncio.sleep(1)
        
        async with await self.api.post(f"/quests/{qid}/video-progress", {"timestamp": needed}):
            pass
        await self.log_to_bot(f"Xong: {name}", "ok")

    async def complete_heartbeat(self, quest: dict):
        name, qid, tt = get_quest_name(quest), quest["id"], get_task_type(quest)
        needed, done = get_seconds_needed(quest), get_seconds_done(quest)
        await self.log_to_bot(f"🎮 {tt}: {name} (~{(needed-done)//60} phút còn lại)", "info")
        pid = random.randint(1000, 30000)
        while done < needed and self.is_running:
            try:
                async with await self.api.post(f"/quests/{qid}/heartbeat", {"stream_key": f"call:0:{pid}", "terminal": False}) as r:
                    if r.status == 200:
                        body = await r.json()
                        done = body.get("progress", {}).get(tt, {}).get("value", done)
                        await self.log_to_bot(f"  {name}: {done:.0f}/{needed}s", "progress")
                        if body.get("completed_at") or done >= needed:
                            await self.log_to_bot(f"Xong: {name}", "ok")
                            return
                    elif r.status == 429:
                        await asyncio.sleep((await r.json()).get("retry_after", 10) + 1)
                        continue
            except Exception: pass
            await asyncio.sleep(quest_config.HEARTBEAT_INTERVAL)
        
        async with await self.api.post(f"/quests/{qid}/heartbeat", {"stream_key": f"call:0:{pid}", "terminal": True}):
            pass

    async def process_quest(self, quest: dict):
        qid, name, tt = quest.get("id"), get_quest_name(quest), get_task_type(quest)
        if not tt or qid in self.completed_ids: return
        await self.log_to_bot(f"━━━ Bắt đầu: {name} (nhiệm vụ: {tt}) ━━━", "info")
        if tt in ("WATCH_VIDEO", "WATCH_VIDEO_ON_MOBILE"): 
            await self.complete_video(quest)
        elif tt in ("PLAY_ON_DESKTOP", "STREAM_ON_DESKTOP", "PLAY_ACTIVITY"): 
            await self.complete_heartbeat(quest)
        self.completed_ids.add(qid)

    async def run(self):
        global actionable
        await self.log_to_bot("="*40, "info")
        await self.log_to_bot("TỰ ĐỘNG CÀY QUEST DISCORD V3.0 (Async)", "info")
        await self.log_to_bot("="*40, "info")
        while self.is_running:
            quests = await self.fetch_quests()
            if quests:
                completed_count = sum(1 for q in quests if is_completed(q))
                await self.log_to_bot(f"Tổng: {len(quests)} | Đã xong: {completed_count}", "info")
                quests = await self.auto_accept(quests)
                actionable = [q for q in quests if is_enrolled(q) and not is_completed(q) and is_completable(q) and q.get("id") not in self.completed_ids]
                for q in actionable: 
                    if not self.is_running: break
                    await self.process_quest(q)
            
            # Kiểm tra xem tất cả các quest đã hoàn thành chưa
            if actionable: # Vừa xử lý xong một số quest
                 quests = await self.fetch_quests()
            
            all_done = all(is_completed(q) or not is_completable(q) for q in (quests or []))
            if all_done and quests:
                await self.log_to_bot("✅ Tất cả Quest hiện tại đã hoàn thành", "ok")
                break

            await asyncio.sleep(quest_config.POLL_INTERVAL)

    def stop(self):
        self.is_running = False

async def start_quest_auto(token: str, bot=None, chat_id=None):
    async with aiohttp.ClientSession() as session:
        build_number = await fetch_latest_build_number(session)
        api = AsyncDiscordAPI(token, build_number, session)
        user_info = await api.validate_token()
        if user_info:
            completer = AsyncQuestAutocompleter(api, bot, chat_id)
            await completer.log_to_bot(f"🚀 Đã xác thực Discord: <b>{user_info['username']}</b>. Bắt đầu quét Quest...", "ok")
            await completer.run()
            return True
        else:
            return False
