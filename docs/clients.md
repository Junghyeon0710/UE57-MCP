# 클라이언트 연결

먼저 README의 엔진 플러그인 조립·설치를 완료하고 UE 5.7 에디터에서 프로젝트를 엽니다. 기본 주소는 `http://127.0.0.1:8000/mcp`입니다. 설치기는 해당 포트의 자동 시작을 로컬 Saved 설정에 등록합니다.

## Claude Code

```text
/plugin marketplace add Junghyeon0710/UE57-MCP
/plugin install ue57-mcp@ue57-mcp
```

설치된 플러그인의 `.mcp.json`은 `unreal-mcp-57` 연결을 기본 8000 포트에 만듭니다. `/mcp`에서 연결을 확인합니다. 스킬·훅 설치만으로 엔진 플러그인이 설치되거나 에디터가 실행되지는 않습니다.

수동 등록을 선호하면 Claude Code의 MCP 설정에 다음을 추가합니다.

```json
{
  "mcpServers": {
    "unreal-mcp-57": {"type": "http", "url": "http://127.0.0.1:8000/mcp"}
  }
}
```

`hooks/unreal-context.py`는 Python 3.10 이상이 필요합니다. 프로젝트 하위 폴더에서도 상위 `.uproject`를 찾아 짧은 UE 5.7 문맥을 제공합니다. 훅 실패와 MCP 서버 연결 실패는 별도로 확인합니다.

## Codex

```powershell
codex mcp add unreal-mcp-57 --url http://127.0.0.1:8000/mcp
codex mcp list
```

또는 로컬 `~/.codex/config.toml`에 다음을 등록합니다. HTTP 서버의 `url` 설정 형식은 [OpenAI 공식 MCP 연결 문서](https://developers.openai.com/learn/docs-mcp)를 참고했습니다.

```toml
[mcp_servers.unreal-mcp-57]
url = "http://127.0.0.1:8000/mcp"
```

사용 지침이 필요하면 이 저장소의 `skills/ue57-mcp` 폴더를 자신의 Codex 스킬 경로에 복사할 수 있습니다. 저장소 설치기는 기존 사용자 Codex 설정을 자동으로 덮어쓰지 않습니다.

## 다른 포트

설치할 때 `install --port 8001`을 사용하거나 에디터 콘솔에서 `ModelContextProtocol.StartServer 8001`을 실행합니다. 클라이언트 URL과 검증기의 `--url`도 같은 포트로 바꿉니다. Claude 플러그인 기본 `.mcp.json`의 8000과 다르면 수동 MCP 설정을 사용합니다.

```powershell
python scripts/ue57_mcp.py verify --url http://127.0.0.1:8001/mcp
```

연결되면 먼저 `list_toolsets`, 다음으로 `describe_toolset`, 마지막으로 스키마에 맞는 `call_tool`을 순차 호출합니다. 도구 이름과 인수는 실행 중인 에디터가 반환한 값을 따릅니다.
