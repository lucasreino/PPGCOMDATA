from typing import Any, Optional

from pydantic import BaseModel


class ProfessorCadastroResponse(BaseModel):
    professor_id: str
    nome_completo: str
    id_lattes: Optional[str] = None
    foto_url: Optional[str] = None
    xml_importado: bool = False
    upload_id: Optional[str] = None
    upload_status: Optional[str] = None
    metrics: Optional[dict[str, Any]] = None
    cadastro_oficial: bool = True
    linha_oficial: Optional[str] = None
    mensagem: str = "Docente cadastrado com sucesso."
