@echo off

REM Verifica se a mensagem foi passada
IF "%~1"=="" (
    echo Usa: git-commit-push "mensagem do commit"
    exit /b 1
)

REM Mostra a mensagem
echo Mensagem do commit: %~1

REM Adiciona ficheiros
git add .

REM Faz commit
git commit -m "%~1"

REM Faz push
git push

echo ---
echo Operacao concluida!
