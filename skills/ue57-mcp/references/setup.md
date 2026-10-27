# Connection and installation

The full editor plugins are installed by the repository's `Install.cmd`. The installer requires UE 5.7.4, Git with Epic UnrealEngine access, and Visual Studio C++ tools. It fetches only required 5.8 originals and builds against 5.7; a 5.8 engine installation is unnecessary.

Open the installed project and connect to `http://127.0.0.1:8000/mcp`, or its configured port. Check the repository's `scripts/verify.py` against the live endpoint; expected registration is 55 toolsets / 858 tools.

If the client exposes `ue57.*` groups, it is connected to the old reduced implementation. Stop that server, use the full backport installation, and refresh client tool discovery. Do not invent mappings between the two interfaces.
