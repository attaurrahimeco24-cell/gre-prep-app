import time
import logging
from typing import Dict, Any, Optional
import gre_platform_merged as config
import gre_platform_merged as db_manager

logger = logging.getLogger("GRE_PLATFORM.timer")

class TimerExpiredError(Exception):
    pass

def start_section_timer(section_instance_id: str) -> float:
    start_ts = db_manager.start_session_section(section_instance_id)
    logger.info("Timer started for section %s at epoch %f", section_instance_id, start_ts)
    return start_ts

def get_section_time_status(section_instance_id: str, duration_seconds: int) -> Dict[str, Any]:
    with db_manager.db_cursor() as cur:
        cur.execute(
            "SELECT section_start_timestamp, status FROM session_sections WHERE section_instance_id = ?",
            (section_instance_id,)
        )
        row = cur.fetchone()
        
    if not row or not row["section_start_timestamp"]:
        return {
            "start_timestamp": None,
            "elapsed_seconds": 0,
            "remaining_seconds": duration_seconds,
            "formatted_time": format_seconds_display(duration_seconds),
            "is_expired": False,
            "status": "pending"
        }
        
    start_ts = row["section_start_timestamp"]
    now = time.time()
    elapsed = int(now - start_ts)
    remaining = max(0, duration_seconds - elapsed)
    is_expired = remaining <= 0 or row["status"] == "completed"
    
    return {
        "start_timestamp": start_ts,
        "elapsed_seconds": elapsed,
        "remaining_seconds": remaining,
        "formatted_time": format_seconds_display(remaining),
        "is_expired": is_expired,
        "status": row["status"]
    }

def format_seconds_display(seconds: int) -> str:
    if seconds < 0:
        return "00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def get_question_elapsed_time(question_start_ts: float) -> int:
    if not question_start_ts:
        return 0
    return max(1, int(time.time() - question_start_ts))