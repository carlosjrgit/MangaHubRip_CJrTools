@echo off
chcp 65001 >nul
title MangaHubRip CJrTools (Modo Desenvolvimento)
cd /d "%~dp0"

echo ======================================================
echo   MangaHubRip CJrTools - Executando via Codigo Fonte
echo   (Alteracoes no codigo terao efeito imediato)
echo ======================================================
echo.

python mangadex_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu uma falha na execucao do programa.
    echo Pressione qualquer tecla para fechar esta janela...
    pause >nul
)
