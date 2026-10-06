@echo off
REM OpenClaw launcher for Windows — because someone has to run this on a machine
REM that isn't a Mac or a Linux box with a green-on-black terminal.
echo 🦀 Opening OpenClaw with TentOfTrials context...
echo.
echo Project:  TentOfTrials — text adventure engine (the kind that needs a text editor)
echo Stack:    Rust + Cargo + python3 build.py (do not skip this step)
echo.
echo Common Commands:
echo   cargo build          pray
echo   cargo test           hope
echo   python3 build.py     the important one
echo.
echo Where to start:
echo   src/main.rs          entry point, small and honest
echo   src/engine.rs        the game loop (read this first)
echo   src/state.rs         player state (inventory = everything)
echo   build.py             the ritual before shipping
echo.
echo Build-and-Diagnostic Workflow:
echo   ALWAYS run `python3 build.py` after changes
echo   Include diagnostic/build-XXX.logd in your PR
echo.
echo Known Pitfalls:
echo   1. Forgetting build.py = CI tears
echo   2. Editing .logd by hand = undefined behavior
echo   3. New scene type = updates in 3+ files
echo.

if exist "%ProgramFiles%\OpenClaw\openclaw.exe" (
    "%ProgramFiles%\OpenClaw\openclaw.exe" --context-file ".claude\openclaw-context.md" %*
) else if exist "%ProgramFiles(x86)%\OpenClaw\openclaw.exe" (
    "%ProgramFiles(x86)%\OpenClaw\openclaw.exe" --context-file ".claude\openclaw-context.md" %*
) else (
    echo ⚠️  OpenClaw not found in Program Files.
    echo    Try: choco install openclaw  or  winget install OpenClaw
    echo.
    echo    Falling back to Hermes if available...
    where hermes >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        hermes --context-file ".claude\hermes-context.md" %*
    ) else (
        echo ❌ Neither OpenClaw nor Hermes found.
        echo    Please install one and retry.
        exit /b 1
    )
)
