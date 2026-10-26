@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Tela Livre - instalador
echo.
echo  ===== Tela Livre: tela inicial sem anuncios para TVs Samsung (2016 a 2022) =====
echo.
set TVIP=
if exist tv-ip.txt set /p TVIP=<tv-ip.txt
if defined TVIP (echo  TV: %TVIP%   [apague tv-ip.txt para trocar]) else (set /p TVIP= Digite o IP da TV, ex: 192.168.0.20: )
if not defined TVIP goto erro
> tv-ip.txt echo %TVIP%
set BUILD=
if not exist config.properties set BUILD=--generic
echo.
echo  [1/4] Preparando a ferramenta de assinatura...
py -3 -m pip install --user --quiet --disable-pip-version-check cryptography > instalar-log.txt 2>&1 || goto erro
echo  [2/4] Montando o app...
py -3 tizen\build.py %BUILD% >> instalar-log.txt 2>&1 || goto erro
echo  [3/4] Assinando o app.
echo        Na primeira vez, CRIE uma senha (ela nao aparece enquanto digita) e guarde.
echo        Nas proximas atualizacoes, use a mesma senha.
py -3 tizen\sign.py 2>> instalar-log.txt || goto erro
echo  [4/4] Enviando pra TV. Olhe a TV: se aparecer algum aviso, aceite.
py -3 tizen\install.py %TVIP% >> instalar-log.txt 2>&1 || goto erro
echo.
echo  PRONTO! O Tela Livre deve abrir na TV agora.
echo.
pause
exit /b 0
:erro
echo.
echo  Deu erro. Veja o arquivo instalar-log.txt nesta pasta.
echo.
pause
exit /b 1
