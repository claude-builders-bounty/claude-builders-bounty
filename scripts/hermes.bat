@echo off
REM Hermes launcher for Windows — Hermes delivers, allegedly.
echo 🐉 Opening Hermes with TentOfTrials context...
echo.
echo Project:  TentOfTrials — interactive fiction in Rust
echo Stack:    Rust 2021, serde, clap, anyhow, env_logger
echo.
echo Common Commands:
echo   cargo check          quick compile check
echo   cargo test           integration tests
echo   python3 build.py     ⚠️  REQUIRED before PR
echo   cargo clippy         don't ignore this
echo.
echo Where to start:
echo   src/main.rs          bootstrap
echo   src/engine.rs        core loop
echo   src/state.rs         player model
echo   build.py             the gatekeeper
echo.
echo Build-and-Diagnostic Workflow:
echo   ALWAYS run `python3 build.py` after changes
echo   Artifacts: diagnostic/build-XXX.logd (+ .json if present)
echo.
echo Known Pitfalls:
echo   1. Stale build artifacts = failing CI
echo   2. .logd is machine-generated — do not hand-edit
echo   3. Scene serialization = strict ordering
echo.

if exist "%ProgramFiles%\Hermes\hermes.exe" (
    "%ProgramFiles%\Hermes\hermes.exe" --context-file ".claude\hermes-context.md" %*
) else if exist "%ProgramFiles(x86)%\Hermes\hermes.exe" (
    "%ProgramFiles(x86)%\Hermes\hermes.exe" --context-file ".claude\hermes-context.md" %*
) else (
    echo ⚠️  Hermes not found in Program Files.
    echo    Try: choco install hermes  or  winget install Hermes
    echo.
    echo    Falling back to OpenClaw if available...
    where openclaw >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        openclaw --context-file ".claude\openclaw-context.md" %*
    ) else (
        echo ❌ Neither Hermes nor OpenClaw found.
        echo    Please install one and retry.
        exit /b 1
    )
)
