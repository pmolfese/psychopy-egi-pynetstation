@ECHO OFF

pushd %~dp0

if "%SPHINXBUILD%" == "" set SPHINXBUILD=python -m sphinx
if "%SPHINXOPTS%" == "" set SPHINXOPTS=-W --keep-going

%SPHINXBUILD% -M %1 . _build %SPHINXOPTS%
popd
