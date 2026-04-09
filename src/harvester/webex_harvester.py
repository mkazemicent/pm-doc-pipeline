"""Harvest meeting transcripts and space messages from Webex."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .base import BaseHarvester


class WebexHarvester(BaseHarvester):
    """Pull transcripts and messages from Cisco Webex."""

    def __init__(self, config: dict, raw_dir: Path):
        super().__init__(config, raw_dir)
        self.source_cfg = config.get("sources", {}).get("webex", {})

    def harvest(self) -> list[Path]:
        if not self.source_cfg.get("enabled"):
            self.log.info("Webex source is disabled, skipping.")
            return []

        from webexpythonsdk import WebexAPI

        token = os.environ.get("WEBEX_ACCESS_TOKEN", "")
        if not token:
            self.log.warning("WEBEX_ACCESS_TOKEN not set.")
            return []

        api = WebexAPI(access_token=token)
        downloaded: list[Path] = []
        lookback = self.source_cfg.get("lookback_days", 30)
        since = datetime.now(timezone.utc) - timedelta(days=lookback)

        # Meeting transcripts
        for meeting_id in self.source_cfg.get("meeting_ids", []):
            self.log.info("Fetching transcript for meeting: %s", meeting_id)
            try:
                transcripts = api.meeting_transcripts.list(meetingId=meeting_id)
                for transcript in transcripts:
                    content = api.meeting_transcripts.download(transcript.id)
                    fname = f"meeting_{meeting_id}_{transcript.id}.vtt"
                    downloaded.append(self._write_raw(fname, content, subdir="webex/transcripts"))
            except Exception as exc:
                self.log.error("Failed to fetch transcript for %s: %s", meeting_id, exc)

        # Room / Space messages
        for room_id in self.source_cfg.get("room_ids", []):
            self.log.info("Fetching messages from room: %s", room_id)
            try:
                messages = api.messages.list(roomId=room_id)
                room_msgs = []
                for msg in messages:
                    msg_time = datetime.fromisoformat(msg.created.replace("Z", "+00:00"))
                    if msg_time < since:
                        break
                    room_msgs.append({
                        "id": msg.id,
                        "author": msg.personEmail,
                        "text": msg.text or "",
                        "created": msg.created,
                    })
                if room_msgs:
                    fname = f"room_{room_id}_{self._timestamp()}.json"
                    downloaded.append(
                        self._write_raw(fname, json.dumps(room_msgs, indent=2), subdir="webex/rooms")
                    )
            except Exception as exc:
                self.log.error("Failed to fetch room %s: %s", room_id, exc)

        self.log.info("Webex: harvested %d items.", len(downloaded))
        return downloaded
