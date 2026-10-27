#!/usr/bin/env python3
"""프로젝트가 확인될 때만 5.7 MCP 사용 문맥을 제공한다."""
import json
import os
from pathlib import Path

def context(start):
    path=Path(start).resolve()
    for directory in [path,*path.parents]:
        projects=sorted(directory.glob("*.uproject"))
        if projects:
            return (f"Unreal Engine project: {projects[0].name}. Use the ue57-mcp skill for live editor actions. "
                    "Discover current tool schemas before calling tools. This UE 5.7 backport has documented 5.8 feature limits.")
    return None

if __name__=="__main__":
    message=context(os.getcwd())
    if message:print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":message}}))
