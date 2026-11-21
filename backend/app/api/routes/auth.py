from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ContainerDep
from app.schemas.auth import LoginSchema, VerifySchema

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/auth/status")
async def auth_status(c: ContainerDep):
    return {"authorized": c.is_authorized}


@router.post("/auth/login")
async def login(data: LoginSchema, c: ContainerDep):
    await c.session.request_code(data.api_id, data.api_hash, data.phone)
    return {"status": "awaiting_code", "mensagem": "Credenciais salvas e código enviado!"}


@router.post("/auth/verify")
async def verify(data: VerifySchema, c: ContainerDep):
    result = await c.session.verify_code(data.phone, data.code, data.password)
    if result.needs_password:
        return {"status": "needs_password", "mensagem": "Sua conta possui Verificação em Duas Etapas (2FA)."}

    # Antes os workers só eram criados no startup: depois de um login novo o
    # start-upload falhava até reiniciar o servidor.
    await c.pool.setup()
    # A string de sessão (equivale a uma senha da conta) fica só no banco do servidor:
    # o front nunca a usou e ela não deve trafegar.
    return {"status": "success", "mensagem": "Autenticado com sucesso! Redirecionando..."}


@router.get("/user/me")
async def me(c: ContainerDep):
    return await c.session.current_user()
