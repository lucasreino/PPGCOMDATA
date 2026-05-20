from app.services.professor_lookup import find_professor, normalize_text
from app.models.core import Professor


def test_normalize_text_ignores_accents():
    assert normalize_text("José Carlos") == normalize_text("Jose Carlos")


def test_find_professor_by_normalized_name():
    profs = [
        Professor(
            nome_completo="José Carlos Messias Santos Franco",
            email="jose.cmsf@ufma.br",
            id_lattes="8042448829229400",
        )
    ]
    found = find_professor(
        None,
        nome_completo="Jose Carlos Messias Santos Franco",
        candidates=profs,
    )
    assert found is profs[0]
