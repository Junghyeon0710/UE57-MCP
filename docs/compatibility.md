# 지원 범위

검증 대상은 UE **5.7.4 Win64 Editor**, 조립 원본은 **5.8.4**입니다. 공식 AllToolsets의 의존 플러그인 21개를 포함하고, 별도 MVVM·Cloth·MetaHuman 관련 도구를 추가합니다. 등록 결과는 55개 도구 모음·858개 도구이며 모든 입력 조합의 동작 보증을 뜻하지 않습니다.

| 범위 | 내용 |
|---|---|
| 일반 에디터 | Actor·Asset·Blueprint·Material·데이터 테이블·로그·컴파일·자동화 테스트 |
| 애니메이션 | Sequencer·키프레임·바인딩 태그/조건/이징·Control Rig·FBX/AnimSequence 입출력 |
| UMG / MVVM | 위젯 트리 편집, ViewModel·바인딩·변환 함수, MVVM 참조를 유지하는 위젯 교체 |
| Niagara | 기존 정보·컴포넌트·에셋 도구와 System 편집 도구 46개 |
| Dataflow / Cloth | 그래프·핀·변수·템플릿·호환 에셋 생성, 기존 의상 바인딩과 Chaos Cloth 변환 |
| PCG | 그래프·파라미터·실행 결과의 메타데이터·Skill 에셋 8개·스플라인 도구 |
| Gameplay | GAS·Gameplay Tags·StateTree·Physics·Conversation 조회·Game Features |
| MetaHuman | 기본 캐릭터 에셋·편집 세션·몸/피부/눈 설정 도구 |
| Semantic Search | Search·FindSimilar·색인 관리 및 별도 Tools → Semantic Search 창 |

## 엔진 버전 제한

- **Sequencer Animation Mixer의 새 레이어·전환**: 5.7에 해당 런타임 및 관련 UAF 구현이 없어 플러그인을 활성화하지 않습니다.
- **Cloth**: 5.8 전용 `InnerCollisionThickness`, 물과 상호작용하는 Aerodynamics 속성, `FictitiousForcesModel` 등은 5.7에서 재현하지 않습니다. `StripUserAttributes` 노드를 우회한 31개 노드·36개 연결의 5.7용 변환 템플릿을 생성합니다. 5.8 물리 결과와의 동일성은 보증하지 않습니다.
- **5.8 전용 엔진 노드·에셋**: 5.7에 자동 추가되지 않습니다. PCG Skill의 지침은 복원하지만, 지침에서 참조하는 5.8 전용 PCGPrimitives 등은 5.7의 노드·에셋으로 별도 구성해야 합니다.
- **PCG DrawSpline**: 원본 대화형 뷰포트 작업입니다. 명시적 좌표로 즉시 생성하려면 `CreateSplineFromPoints`를 사용합니다. 사용자 드로잉 과정은 전수 검증하지 않았습니다.
- **Semantic Search UI**: 5.8 콘텐츠 브라우저 검색창의 대체 API를 대신해 별도 검색 창에서 결과 선택과 브라우저 이동을 연결합니다.
- **SSE**: 5.7 HTTPServer에 다중 응답 API가 없어 단일 JSON 결과를 반환합니다.

## 추가 구성 요소

MetaHuman의 전체 캐릭터 생성·미리보기·텍스처 작업에는 Epic Games Launcher의 UE 5.7 설치 옵션에서 **MetaHuman Creator Core Data**를 추가해야 합니다. 설치기는 이를 대신 다운로드하지 않습니다. 기본 설정 도구 검사와 완성된 캐릭터 생성은 다른 검증 범위입니다.

Game Features 도구의 활성화 효과는 실제 프로젝트의 Game Feature 플러그인과 데이터에 달려 있습니다. 설치기는 에디터 전용 GameFeatureData 타입을 로컬 AssetManager 설정에 등록합니다. 게임의 네트워크·RPC·복제 코드를 추가하지 않습니다.

## Semantic Search 모델 설정

검색 기능은 에셋 설명을 만드는 모델과 텍스트 임베딩 모델을 사용합니다. 서버는 사용자의 컴퓨터에서 실행하는 OpenAI 호환 API일 수도 있고 별도 서비스일 수도 있습니다. 엔진 MCP 서버와 모델 서버는 역할이 다릅니다.

1. **Editor Preferences → Plugins → Semantic Search**를 엽니다.
2. 작은 콘텐츠 폴더를 Indexed Paths에 지정합니다.
3. `Captioning Base URL`과 `Captioning Model`에 이미지·구조화된 JSON 응답을 지원하는 모델을 지정합니다. URL은 `/v1` 같은 API 기본 경로까지 입력합니다. 플러그인이 `/chat/completions`를 붙입니다.
4. `Embedding Base URL`, `Embedding Model`, `Embedding Dimension`을 실제 모델에 맞춥니다. 플러그인은 `/embeddings`로 `dimensions`를 전송합니다.
5. 인증이 필요한 경우 API Key는 로컬 설정에 입력합니다.
6. `SemanticSearch.IndexAll`로 색인하고 `SemanticSearch.IndexStats` 또는 색인 관리 창으로 상태를 확인합니다.

모델이나 차원을 바꾸면 다시 색인합니다. 모델 설정 전에는 안내 오류를 반환하며 자동 색인은 기본으로 끕니다. 색인 과정에서 선택한 에셋의 썸네일·메타데이터와 설명이 설정한 서버로 전달됩니다. 고정 응답 테스트는 HTTP·색인·검색 경로를 검증하며 실제 모델의 자연어 이해나 검색 품질 검증은 아닙니다.
