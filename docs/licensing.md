# 배포 범위와 라이선스

Epic의 공개 [Claude Code 스킬 예제](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin)는 MIT 라이선스의 지침·훅 패키지입니다. Unreal Engine 설치 폴더에서 가져온 MCP와 Editor 도구 전체가 MIT라는 뜻은 아닙니다.

[Unreal Engine EULA](https://www.unrealengine.com/eula/unreal)의 5(a)와 6(d)는 엔진 코드와 Engine Tools의 배포 조건을 정합니다. 따라서 이 독립 공개 저장소에는 엔진 원본·엔진 파생 콘텐츠·컴파일된 엔진 도구를 넣지 않습니다. 이를 공개할 적절한 권한이 별도로 확인되지 않은 상태에서 로컬 생성물을 릴리스에 첨부하지 않습니다.

공개하는 것은 다음입니다.

- 일반 설치기·검증기·로컬 에셋 재생성 스크립트
- 사용자가 보유한 원본 파일의 상대 경로·SHA256·줄 범위를 참조하는 조립 레시피
- 독자적으로 작성한 호환 변경과 설정
- Epic의 MIT 고지를 보존한 사용 스킬 및 자체 훅

레시피는 엔진 원본을 압축·인코딩한 대체물이 아닙니다. `copy` 연산은 로컬 엔진 또는 고정된 공개 호환 의존성의 파일이 있을 때만 동작합니다. 원본 해시가 다르거나 원본이 없으면 조립하지 않습니다. 엔진 원본의 대량 추가 구문은 공개 의존성 패치 또는 로컬 원본의 참조로 남깁니다.

최초 조립 시 라이선스를 보유한 UE 5.7.4·5.8.4 설치본과 고정 PortKit 의존성이 필요합니다. 조립 결과에는 Engine Code가 있으므로 **Apache-2.0이나 MIT로 재라이선스되지 않습니다.** 엔진 EULA 및 각 ThirdParty 라이선스를 따릅니다. 작업 폴더와 설치된 플러그인 전체는 공개 저장소의 소스·릴리스에 포함하지 않습니다.

이 저장소의 일반 설치 코드와 독자 변경에는 Apache-2.0, Epic 공개 스킬에서 가져온 부분에는 `LICENSES/Epic-skills-MIT.txt`가 적용됩니다. PortKit의 자체 코드 라이선스는 해당 고정 의존성의 LICENSE에서 확인합니다. `NOTICE`에 출처와 고정 커밋을 기록했습니다.
