# UE 5.7 전용 ZIP

완성 패키지는 UE 5.7.4 Win64 에디터에서 실행할 DLL, 호환 소스, ThirdParty 라이브러리, PCG Skill 8개와 Cloth 템플릿을 포함합니다. 받는 사용자는 **5.8 설치·5.8 실행·플러그인 컴파일 없이** 설치할 수 있습니다. 검증한 엔진은 Epic Launcher 5.7.4, BuildId `47537391`입니다. 다른 버전이나 소스 빌드의 바이너리 호환성을 보장하지 않습니다.

## 다운로드 상태

현재 독립 공개 저장소에는 엔진 파생 ZIP을 올리지 않았으며 공개 다운로드 주소도 제공하지 않습니다. [Epic EULA](https://www.unrealengine.com/eula/unreal)의 Engine Tools 배포 조건에 맞는 Fab 또는 Epic UnrealEngine GitHub fork 배포가 별도로 필요합니다. Epic GitHub fork를 이용한다면 해당 엔진 저장소 접근 권한이 필요하지만 **5.8 설치는 필요하지 않습니다.** 설치기가 접근 권한을 우회하지 않습니다.

이미 적법하게 받은 ZIP이 있으면 [README의 install-prebuilt 명령](../README.md#ue-57만-설치한-사용자)으로 설치합니다. 게시자가 제공한 SHA256과 다음 결과를 비교한 뒤 사용합니다.

```powershell
Get-FileHash 'C:/Downloads/UE57-MCP-5.7.4-Win64.zip' -Algorithm SHA256
```

패키지 내부 파일 해시는 손상을 검출합니다. 출처 인증을 대신하지 않으므로 신뢰하는 게시자의 배포물만 실행합니다.

## 제작

원본 조립과 5.7 빌드·에셋 재생성을 완료한 제작자가 실행합니다.

```powershell
python scripts/ue57_mcp.py pack-prebuilt `
  --bundle 'C:/UE57MCPBuild/host57/Plugins/UE57MCP' `
  --engine57 'C:/Epic/UE_5.7' `
  --output 'C:/UE57Packages/UE57-MCP-5.7.4-Win64.zip'
```

모든 모듈의 BuildId와 DLL, 원본 조립 해시, 에셋 완료 상태를 검사합니다. 실행에 필요한 DLL과 원본 ThirdParty LIB를 포함하고 Intermediate·Saved·PDB·생성된 링크용 LIB는 제외합니다. ZIP 내부 `prebuilt.json`에 엔진 버전, BuildId, 파일별 SHA256을 기록합니다. 기존 출력 파일은 덮어쓰지 않습니다.

이 ZIP은 Apache-2.0으로 재라이선스되지 않습니다. 엔진 EULA와 포함된 ThirdParty 조건을 따르며, 이 공개 저장소의 커밋·릴리스에 첨부하지 않습니다. [라이선스 안내](licensing.md)
