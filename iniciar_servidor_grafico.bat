@echo off
echo Iniciando Servidor X (VcXsrv) para Gazebo en WSL2...
start "" "C:\Program Files\VcXsrv\vcxsrv.exe" :0 -multiwindow -clipboard -wgl -ac
echo ¡Servidor iniciado! Ya puedes ejecutar Gazebo en tu terminal de WSL.
exit
