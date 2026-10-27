#!/usr/bin/env python3
"""공개 대상에 엔진 산출물·개인 경로·API 비밀 값이 섞이지 않는지 확인한다."""
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIX={".uasset",".umap",".dll",".exe",".lib",".pdb",".patch",".rej",".orig",".zip"}

def check():
    # Git이 공개 대상으로 보는 파일만 검사하여 무시된 로컬 조립 결과는 읽지 않는다.
    names=subprocess.check_output(["git","-C",str(ROOT),"ls-files","--cached","--others","--exclude-standard","-z"]).decode().split("\0")
    errors=[]
    for name in filter(None,names):
        path=ROOT/name
        if path.suffix.lower() in FORBIDDEN_SUFFIX:
            errors.append(f"Restricted source/binary type: {name}")
            continue
        text=path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() in {".cpp",".h"} and (not name.startswith("Optional/UE57MCPNative/Source/") or "SPDX-License-Identifier: Apache-2.0" not in text or "Copyright Epic" in text):
            errors.append(f"Unreviewed native source provenance: {name}")
        if re.search(r"[A-Z]:[/\\](?:Users|Unreal Projects|Epic Games)[/\\]",text):errors.append(f"Private absolute path: {name}")
        if re.search(r"\bsk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{20,}",text):errors.append(f"Possible secret: {name}")
    if errors:raise SystemExit("\n".join(errors))
    print(f"Public tree checked: {len(list(filter(None,names)))} files; original plugin source only, no engine files/binaries or private paths")

if __name__=="__main__":check()
