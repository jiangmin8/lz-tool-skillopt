"""SkillOpt-Sleep — Custom harvest source for agent_trace.jsonl format.

Supports the custom format:
{"timestamp": "2026-06-15 17:07:21", "messages": [{"role": "user", "content": "..."}]}
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

from skillopt_sleep.types import SessionDigest


def _iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return


def _detect_feedback(text: str) -> List[str]:
    low = text.lower()
    sig: List[str] = []
    neg_phrases = ("still broken", "doesn't work", "not working", "wrong", 
                   "error", "broken", "fix", "failed", "revert", "undo")
    pos_phrases = ("thanks", "thank you", "perfect", "great", "works", 
                   "fixed", "correct", "nice", "awesome")
    for ph in neg_phrases:
        if ph in low:
            sig.append("neg:" + ph)
    for ph in pos_phrases:
        if ph in low:
            sig.append("pos:" + ph)
    return sig


def harvest_custom(
    trace_file: str,
    *,
    since_iso: Optional[str] = None,
    limit: int = 0,
) -> List[SessionDigest]:
    """Harvest sessions from custom agent_trace.jsonl format."""
    digests: List[SessionDigest] = []
    if not os.path.exists(trace_file):
        return digests

    session_id = 0
    for rec in _iter_jsonl(trace_file):
        timestamp = rec.get("timestamp", "")
        messages = rec.get("messages", [])
        
        user_prompts: List[str] = []
        assistant_finals: List[str] = []
        tools: List[str] = []
        feedback: List[str] = []
        n_user = 0
        n_asst = 0

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if isinstance(content, dict):
                content = str(content)
            
            if role == "user":
                n_user += 1
                user_prompts.append(content.strip())
                feedback.extend(_detect_feedback(content))
            elif role == "assistant":
                n_asst += 1
                assistant_finals.append(content.strip())
            elif role == "tool":
                tools.append(msg.get("name", ""))

        if n_user == 0 and n_asst == 0:
            continue

        def _dedup(xs: List[str]) -> List[str]:
            seen = set()
            out = []
            for x in xs:
                if x and x not in seen:
                    seen.add(x)
                    out.append(x)
            return out

        digest = SessionDigest(
            session_id=f"custom-{session_id}",
            project="/media/lz/baba/资料",
            git_branch="",
            started_at=timestamp,
            ended_at=timestamp,
            user_prompts=user_prompts,
            assistant_finals=assistant_finals[-5:],
            tools_used=_dedup(tools),
            files_touched=[],
            feedback_signals=feedback,
            n_user_turns=n_user,
            n_assistant_turns=n_asst,
            raw_path=trace_file,
        )
        
        digests.append(digest)
        session_id += 1
        
        if limit and len(digests) >= limit:
            break

    return digests