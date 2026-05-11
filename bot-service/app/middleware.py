from fastapi import Request, HTTPException
from app.auth import decode_access_token
import logging

logger = logging.getLogger(__name__)

async def security_middleware(request: Request, call_next):
    """
    Middleware global para verificar isolamento de dados básico.
    Garante que se houver um empresa_id na query string, ele bate com o token.
    
    IMPORTANTE: Este middleware NÃO protege contra injeção de IDs via PATH PARAMS (ex: /conversas/{telefone}).
    A proteção de path params é responsabilidade do Depends(obter_empresa) em cada endpoint.
    """
    # Lista de caminhos que não precisam de verificação de empresa_id (públicos ou admin master)
    public_paths = ["/webhook", "/docs", "/openapi.json", "/api/admin", "/login"]
    
    if any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)

    # Extrai o token do Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        
        if payload:
            token_empresa_id = payload.get("sub")
            token_role = payload.get("role")
            
            # Se for admin (franqueador), ele pode acessar qualquer coisa
            if token_role == "admin":
                return await call_next(request)
            
            # Verifica se o cliente está tentando injetar um empresa_id diferente via Query
            query_empresa_id = request.query_params.get("empresa_id")
            if query_empresa_id and query_empresa_id != token_empresa_id:
                logger.error(f"TENTATIVA DE VIOLAÇÃO DE ISOLAMENTO: User {token_empresa_id} tentou acessar empresa {query_empresa_id}")
                raise HTTPException(status_code=403, detail="Acesso negado: Isolamento de dados violado.")

    return await call_next(request)
