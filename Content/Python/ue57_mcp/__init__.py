"""독립적으로 작성한 UE 5.7 에디터 MCP의 공개 시작·종료 진입점이다."""
__version__ = "2.0.0"

def start(port=None):
    """에디터에서 사용할 서버와 메인 스레드 실행 큐를 시작한다."""
    from . import bootstrap
    return bootstrap.start(port)

def stop():
    """플러그인 서버와 에디터 틱 콜백을 종료한다."""
    from . import bootstrap
    return bootstrap.stop()
