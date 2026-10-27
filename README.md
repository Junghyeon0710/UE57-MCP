# UE57-MCP

Unreal Engine **5.7.4 Win64 에디터**에서 UE 5.8.4의 MCP와 에디터 도구를 사용하는 로컬 호환 패키지입니다. 검증 구성은 **55개 도구 모음·858개 도구**입니다. Epic의 공식 5.7 배포판은 아닙니다.

이 저장소에는 **설치·조립 코드, 호환 변경 레시피, 에셋 재생성 코드, Claude Code 스킬·훅, 검증 도구**가 있습니다. Unreal Engine 원본 소스나 DLL·LIB·UAsset은 배포하지 않습니다. **최초 조립에는 라이선스를 보유한 UE 5.7.4와 UE 5.8.4 설치본이 모두 필요합니다.** 조립 후 사용할 에디터는 5.7입니다. [배포 방식과 라이선스](docs/licensing.md)

[English](README.en.md) · [지원 범위](docs/compatibility.md) · [검증 기록](docs/verification.json) · [클라이언트 연결](docs/clients.md)

## 준비

- Windows x64, Git, Python 3.10 이상(`python` 명령을 사용할 수 있도록 PATH에 등록)
- Unreal Engine 5.7.4와 5.8.4: **Engine Source** 구성 요소 및 에디터 실행 파일 포함
- UE 5.7 C++ 프로젝트를 빌드할 수 있는 Visual Studio C++ 도구와 Windows SDK
- 빌드·에셋 생성 시간과 디스크 공간. 첫 빌드는 수 분 이상 걸릴 수 있습니다.

현재 레시피는 특정 5.7.4/5.8.4 원본 파일의 SHA256을 검사합니다. 다른 버전이면 파일을 쓰기 전에 중단합니다. 버전 검사만 없애서 다른 엔진에 적용하지 않습니다.

## 설치

아래 명령은 PowerShell 예시입니다. 엔진과 프로젝트 경로를 자신의 환경으로 바꿉니다. Windows 경로 길이 제한을 피하도록 작업 폴더는 짧게 지정합니다.

```powershell
git clone https://github.com/Junghyeon0710/UE57-MCP.git
cd UE57-MCP

python scripts/ue57_mcp.py bootstrap `
  --engine57 'C:/Epic/UE_5.7' `
  --engine58 'C:/Epic/UE_5.8' `
  --work-dir 'C:/UE57MCPBuild'
```

`bootstrap`은 공개 호환 의존성인 [UE57-MCP-PortKit](https://github.com/MC-Oruc/UE57-MCP-PortKit)을 고정된 커밋으로 내려받고, 로컬 원본 참조 927개를 검증해 파일 982개를 조립합니다. 독립 5.7 프로젝트를 빌드하고, 5.8에서 읽은 데이터를 바탕으로 **PCG Skill 8개와 Cloth 템플릿을 5.7 형식으로 다시 저장**합니다. 다운로드한 엔진 코드를 저장소로 업로드하는 동작은 없습니다.

완료 후 사용할 프로젝트의 에디터를 닫고 설치합니다.

```powershell
python scripts/ue57_mcp.py install `
  --bundle 'C:/UE57MCPBuild/host57/Plugins/UE57MCP' `
  --project 'C:/Projects/MyGame/MyGame.uproject'

python scripts/ue57_mcp.py build `
  --engine57 'C:/Epic/UE_5.7' `
  --project 'C:/Projects/MyGame/MyGame.uproject'
```

블루프린트 전용 프로젝트는 검증 호스트에서 빌드한 플러그인을 사용하므로 게임 에디터 타깃 빌드를 건너뜁니다. C++ 프로젝트 에디터 타깃 이름이 `MyGameEditor`와 다르면 `build --target 실제타깃이름`을 추가합니다. 기존 MCP 설치가 있으면 덮어쓰지 않고 중단합니다. 이전 설치를 백업한 뒤 정리하고 실행합니다.

설치 위치는 프로젝트의 `Plugins/UE57MCP`입니다. 플러그인이 로컬에서 기본 활성화되므로 **`.uproject`, `Config/DefaultGame.ini`를 수정하지 않습니다.** 자동 시작 설정은 `Saved/Config/WindowsEditor`에, GameFeatureData 규칙은 로컬 플러그인의 `AllToolsets/Config/Game.ini`에 넣습니다. 기존 프로젝트의 GameFeatureData 규칙이 있으면 유지합니다. Git 프로젝트에서는 `.git/info/exclude`에 플러그인 폴더를 추가하므로 다른 게임 변경을 커밋할 때 함께 추가되지 않습니다. 기존 로컬 설정은 `Saved/UE57MCP/installation-backup.json`에 보관합니다. 변경할 로컬 설정이 이미 Git에 추적 중이면 설치를 중단합니다.

UE 5.7에서 프로젝트를 연 다음 연결을 확인합니다.

```powershell
python scripts/ue57_mcp.py verify --url http://127.0.0.1:8000/mcp
```

`list_toolsets`, `describe_toolset`, `call_tool`이 표시되면 연결된 것입니다. 클라이언트는 스키마를 조회한 뒤 도구를 호출합니다. 설치 과정은 Git 커밋·푸시를 수행하지 않습니다.

## Claude Code / Codex

Claude Code에서 이 저장소의 스킬·훅과 기본 MCP 연결을 설치할 수 있습니다. 이 단계만으로 엔진 플러그인이 설치되는 것은 아니므로 위의 조립·설치부터 완료합니다.

```text
/plugin marketplace add Junghyeon0710/UE57-MCP
/plugin install ue57-mcp@ue57-mcp
```

Codex, 수동 Claude Code 설정, 다른 포트 사용법은 [클라이언트 연결](docs/clients.md)에 있습니다. `hooks/`는 Python을 사용하므로 Git Bash가 필요하지 않습니다.

## 기능과 제한

Actor·Asset·Blueprint·Material·UMG·MVVM·Niagara·Animation/Sequencer·Control Rig·PCG·Dataflow·Cloth·GAS·Gameplay Tags·StateTree·Physics·Conversation·Game Features·MetaHuman 설정·Slate 자동화 도구를 포함합니다. 모든 도구의 모든 인수 조합을 검증했다는 의미는 아닙니다.

- Animation Mixer의 **새 레이어·전환**과 일부 5.8 전용 Cloth 물리 속성·엔진 노드는 포함하지 않습니다.
- MetaHuman의 전체 캐릭터 작업에는 UE 5.7의 **MetaHuman Creator Core Data** 구성 요소가 필요합니다.
- Semantic Search는 **별도 모델 서버 설정**이 필요합니다. 설정 전에는 안내 오류를 반환합니다. Tools → Semantic Search 창을 제공합니다.
- 5.7 HTTPServer 제한으로 MCP 결과는 단일 JSON 응답이며 SSE 진행률 스트리밍은 지원하지 않습니다.
- Win64 에디터용입니다. 게임 패키징, 다른 플랫폼, 모든 에셋 조합은 검증 범위에 포함하지 않습니다.

상세 차이와 모델 설정은 [지원 범위](docs/compatibility.md)를 읽습니다.

## 재시도와 개발

조립 후 빌드를 중단했다면 같은 작업 폴더에서 이어갈 수 있습니다.

```powershell
python scripts/ue57_mcp.py resume --engine57 'C:/Epic/UE_5.7' --engine58 'C:/Epic/UE_5.8' --work-dir 'C:/UE57MCPBuild'
python -m unittest discover -s tests -v
python scripts/check_public_tree.py
```

에셋 생성이 실패해 결과 보고서가 남은 경우에는 원인을 수정하고 **새 작업 폴더**로 재현합니다. 기존 폴더를 자동 삭제하거나 덮어쓰지 않습니다. 빌드 로그와 재생성 데이터는 작업 폴더에 보관합니다. [레시피 구조](docs/recipe-format.md)

프로젝트에서 제거하려면 에디터를 닫고 설치한 `Plugins/UE57MCP`만 제거한 뒤, 설치 백업을 참고해 Saved 설정의 MCP 항목과 GameFeatureData 항목을 복원합니다. 다른 설정은 유지합니다.

## 출처

구조와 에디터 사용 스킬은 [Epic의 공식 공개 예제](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin)를 참고했습니다. 원본 MIT 고지는 `LICENSES/Epic-skills-MIT.txt`에 있습니다. 이 저장소의 설치 코드와 독자 호환 변경은 Apache-2.0입니다. **로컬에서 생성된 엔진 코드에는 이 저장소의 오픈소스 라이선스가 적용되지 않습니다.** `NOTICE`와 [라이선스 설명](docs/licensing.md)을 참고합니다.
