"""Um comando só: monta o front (se precisar) e sobe o back, que serve tudo em http://localhost:5000.

    python start.py             # builda o front só se não existir ou se o código mudou
    python start.py --rebuild   # força o build
    python start.py --no-build  # não mexe no front (só sobe o back)
    python start.py --no-venv   # usa o Python atual, sem criar/usar o venv

Na primeira vez cria o ambiente virtual (./venv) e instala backend/requirements.txt; nas próximas só
reinstala se o requirements.txt mudou. O script se reexecuta com o Python do venv (equivale a ativá-lo).
Precisa de Python e, para o build, de Node com yarn (ou npm).
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONT = ROOT / "frontend"
BACK = ROOT / "backend"
VENV = ROOT / "venv"
REQUIREMENTS = BACK / "requirements.txt"
REQ_MARK = VENV / ".requirements.sha256"
BUILD_INDEX = FRONT / "build" / "index.html"
WATCHED = [FRONT / "src", FRONT / "public", FRONT / "package.json", FRONT / ".env.production"]


def _newest_mtime(paths: list[Path]) -> float:
    newest = 0.0
    for p in paths:
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    newest = max(newest, f.stat().st_mtime)
    return newest


def needs_build() -> bool:
    if not BUILD_INDEX.is_file():
        return True
    return _newest_mtime(WATCHED) > BUILD_INDEX.stat().st_mtime

def front_deps_ok() -> bool:
    """node_modules só vale se o react-scripts está lá e não é mais velho que o package.json/yarn.lock."""
    marker = FRONT / "node_modules" / ".bin" / "react-scripts"
    if not marker.exists():
        return False
    newest_manifest = _newest_mtime([FRONT / "package.json", FRONT / "yarn.lock", FRONT / "package-lock.json"])
    return marker.stat().st_mtime >= newest_manifest

def build_front(force_install: bool = False) -> None:
    tool = shutil.which("yarn") or shutil.which("npm")
    if not tool:
        sys.exit("Node não encontrado. Instale o Node (com yarn ou npm) para montar o front.")
    name = Path(tool).stem.lower()
    run = [tool, "run", "build"] if name == "npm" else [tool, "build"]
    print(f"[start] montando o front com {name}...")
    if force_install or not front_deps_ok():
        print("[start] instalando dependências do front...")
        subprocess.run([tool, "install"], cwd=FRONT, check=True, shell=os.name == "nt")
    subprocess.run(run, cwd=FRONT, check=True, shell=os.name == "nt")


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def in_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV.resolve()


def ensure_venv() -> Path:
    """Cria o venv se faltar e instala os requirements se mudaram. Devolve o python do venv."""
    py = venv_python()
    if not py.exists():
        print(f"[start] criando o ambiente virtual em {VENV}...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        except subprocess.CalledProcessError:
            shutil.rmtree(VENV, ignore_errors=True)  # não deixa um venv pela metade
            sys.exit("Não consegui criar o venv. No Debian/Ubuntu: sudo apt install python3-venv")

    digest = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest() if REQUIREMENTS.is_file() else ""
    if digest and (not REQ_MARK.exists() or REQ_MARK.read_text().strip() != digest):
        print("[start] instalando dependências (requirements.txt)...")
        try:
            subprocess.run([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
        except subprocess.CalledProcessError:
            sys.exit("A instalação das dependências falhou (veja a saída acima).")
        REQ_MARK.write_text(digest)
    return py


def main() -> None:
    args = set(sys.argv[1:])
    if "--no-venv" not in args and not in_venv():
        py = ensure_venv()
        # "ativar" o venv = rodar este mesmo script com o Python dele
        sys.exit(subprocess.call([str(py), str(Path(__file__).resolve()), *sys.argv[1:]]))
    if "--no-build" not in args and FRONT.exists() and ("--rebuild" in args or needs_build()):
        try:
            build_front("--install" in args)
        except subprocess.CalledProcessError:
            sys.exit("O build do front falhou (veja a saída acima). O back não foi iniciado.")
    else:
        print("[start] front já está atualizado.")

    sys.path.insert(0, str(BACK))
    os.chdir(BACK)
    import uvicorn
    from app.core.config import get_settings

    s = get_settings()
    print(f"[start] abra http://{s.host}:{s.port}")
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=False)


if __name__ == "__main__":
    main()