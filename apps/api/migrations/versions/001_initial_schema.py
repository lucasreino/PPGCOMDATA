"""Initial database schema for PPGCOMDATA

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-05-20 11:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create table 'users'
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # 2. Create table 'linhas_pesquisa'
    op.create_table(
        'linhas_pesquisa',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=True),
        sa.Column('status', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_linhas_pesquisa_id', 'linhas_pesquisa', ['id'], unique=False)
    op.create_index('ix_linhas_pesquisa_nome', 'linhas_pesquisa', ['nome'], unique=False)

    # 3. Create table 'professores'
    op.create_table(
        'professores',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome_completo', sa.String(), nullable=False),
        sa.Column('nome_citacao', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('link_lattes', sa.String(), nullable=True),
        sa.Column('id_lattes', sa.String(), nullable=True),
        sa.Column('tipo_docente', sa.String(), nullable=False),
        sa.Column('data_entrada_programa', sa.Date(), nullable=True),
        sa.Column('status', sa.Boolean(), nullable=False),
        sa.Column('observacoes', sa.String(), nullable=True),
        sa.Column('linha_pesquisa_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['linha_pesquisa_id'], ['linhas_pesquisa.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_professores_email', 'professores', ['email'], unique=False)
    op.create_index('ix_professores_id', 'professores', ['id'], unique=False)
    op.create_index('ix_professores_id_lattes', 'professores', ['id_lattes'], unique=False)
    op.create_index('ix_professores_linha_pesquisa_id', 'professores', ['linha_pesquisa_id'], unique=False)
    op.create_index('ix_professores_nome_completo', 'professores', ['nome_completo'], unique=False)
    op.create_index('ix_professores_tipo_docente', 'professores', ['tipo_docente'], unique=False)

    # 4. Create table 'curriculo_uploads'
    op.create_table(
        'curriculo_uploads',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('arquivo_url', sa.String(), nullable=False),
        sa.Column('arquivo_nome', sa.String(), nullable=False),
        sa.Column('ano_inicio', sa.Integer(), nullable=True),
        sa.Column('ano_fim', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('texto_extraido', sa.Text(), nullable=True),
        sa.Column('data_upload', sa.DateTime(), nullable=False),
        sa.Column('data_processamento', sa.DateTime(), nullable=True),
        sa.Column('mensagem_erro', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_curriculo_uploads_id', 'curriculo_uploads', ['id'], unique=False)
    op.create_index('ix_curriculo_uploads_professor_id', 'curriculo_uploads', ['professor_id'], unique=False)
    op.create_index('ix_curriculo_uploads_status', 'curriculo_uploads', ['status'], unique=False)

    # 5. Create table 'pdf_pages'
    op.create_table(
        'pdf_pages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('curriculo_upload_id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('numero_pagina', sa.Integer(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['curriculo_upload_id'], ['curriculo_uploads.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pdf_pages_curriculo_upload_id', 'pdf_pages', ['curriculo_upload_id'], unique=False)
    op.create_index('ix_pdf_pages_id', 'pdf_pages', ['id'], unique=False)
    op.create_index('ix_pdf_pages_professor_id', 'pdf_pages', ['professor_id'], unique=False)

    # 6. Create table 'pdf_sections'
    op.create_table(
        'pdf_sections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('curriculo_upload_id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('nome_secao', sa.String(), nullable=False),
        sa.Column('texto_secao', sa.Text(), nullable=False),
        sa.Column('pagina_inicio', sa.Integer(), nullable=False),
        sa.Column('pagina_fim', sa.Integer(), nullable=False),
        sa.Column('status_extracao', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['curriculo_upload_id'], ['curriculo_uploads.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pdf_sections_curriculo_upload_id', 'pdf_sections', ['curriculo_upload_id'], unique=False)
    op.create_index('ix_pdf_sections_id', 'pdf_sections', ['id'], unique=False)
    op.create_index('ix_pdf_sections_nome_secao', 'pdf_sections', ['nome_secao'], unique=False)
    op.create_index('ix_pdf_sections_professor_id', 'pdf_sections', ['professor_id'], unique=False)

    # 7. Create table 'projetos'
    op.create_table(
        'projetos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('curriculo_upload_id', sa.UUID(), nullable=True),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('situacao', sa.String(), nullable=True),
        sa.Column('ano_inicio', sa.Integer(), nullable=True),
        sa.Column('ano_fim', sa.Integer(), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('papel_docente', sa.String(), nullable=True),
        sa.Column('instituicoes', sa.String(), nullable=True),
        sa.Column('financiamento_mencionado', sa.Boolean(), nullable=False),
        sa.Column('agencia_fomento', sa.String(), nullable=True),
        sa.Column('fonte_dado', sa.String(), nullable=False),
        sa.Column('confianca_ia', sa.String(), nullable=True),
        sa.Column('trecho_original', sa.Text(), nullable=True),
        sa.Column('status_validacao', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['curriculo_upload_id'], ['curriculo_uploads.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projetos_ano_fim', 'projetos', ['ano_fim'], unique=False)
    op.create_index('ix_projetos_ano_inicio', 'projetos', ['ano_inicio'], unique=False)
    op.create_index('ix_projetos_curriculo_upload_id', 'projetos', ['curriculo_upload_id'], unique=False)
    op.create_index('ix_projetos_id', 'projetos', ['id'], unique=False)
    op.create_index('ix_projetos_professor_id', 'projetos', ['professor_id'], unique=False)
    op.create_index('ix_projetos_status_validacao', 'projetos', ['status_validacao'], unique=False)
    op.create_index('ix_projetos_tipo', 'projetos', ['tipo'], unique=False)
    op.create_index('ix_projetos_titulo', 'projetos', ['titulo'], unique=False)

    # 8. Create table 'eventos'
    op.create_table(
        'eventos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('curriculo_upload_id', sa.UUID(), nullable=True),
        sa.Column('nome_evento', sa.String(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=True),
        sa.Column('cidade', sa.String(), nullable=True),
        sa.Column('pais', sa.String(), nullable=True),
        sa.Column('tipo_participacao', sa.String(), nullable=True),
        sa.Column('titulo_trabalho', sa.String(), nullable=True),
        sa.Column('financiamento_mencionado', sa.Boolean(), nullable=False),
        sa.Column('fonte_financiamento', sa.String(), nullable=True),
        sa.Column('fonte_dado', sa.String(), nullable=False),
        sa.Column('confianca_ia', sa.String(), nullable=True),
        sa.Column('trecho_original', sa.Text(), nullable=True),
        sa.Column('status_validacao', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['curriculo_upload_id'], ['curriculo_uploads.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_eventos_ano', 'eventos', ['ano'], unique=False)
    op.create_index('ix_eventos_curriculo_upload_id', 'eventos', ['curriculo_upload_id'], unique=False)
    op.create_index('ix_eventos_id', 'eventos', ['id'], unique=False)
    op.create_index('ix_eventos_nome_evento', 'eventos', ['nome_evento'], unique=False)
    op.create_index('ix_eventos_professor_id', 'eventos', ['professor_id'], unique=False)
    op.create_index('ix_eventos_status_validacao', 'eventos', ['status_validacao'], unique=False)

    # 9. Create table 'producoes'
    op.create_table(
        'producoes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('curriculo_upload_id', sa.UUID(), nullable=True),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('ano', sa.Integer(), nullable=True),
        sa.Column('veiculo', sa.String(), nullable=True),
        sa.Column('doi', sa.String(), nullable=True),
        sa.Column('isbn', sa.String(), nullable=True),
        sa.Column('issn', sa.String(), nullable=True),
        sa.Column('evento_relacionado', sa.String(), nullable=True),
        sa.Column('projeto_relacionado_id', sa.String(), nullable=True),
        sa.Column('fonte_dado', sa.String(), nullable=False),
        sa.Column('confianca_ia', sa.String(), nullable=True),
        sa.Column('trecho_original', sa.Text(), nullable=True),
        sa.Column('status_validacao', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['curriculo_upload_id'], ['curriculo_uploads.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_producoes_ano', 'producoes', ['ano'], unique=False)
    op.create_index('ix_producoes_curriculo_upload_id', 'producoes', ['curriculo_upload_id'], unique=False)
    op.create_index('ix_producoes_doi', 'producoes', ['doi'], unique=False)
    op.create_index('ix_producoes_id', 'producoes', ['id'], unique=False)
    op.create_index('ix_producoes_professor_id', 'producoes', ['professor_id'], unique=False)
    op.create_index('ix_producoes_status_validacao', 'producoes', ['status_validacao'], unique=False)
    op.create_index('ix_producoes_tipo', 'producoes', ['tipo'], unique=False)
    op.create_index('ix_producoes_titulo', 'producoes', ['titulo'], unique=False)

    # 10. Create table 'financiamentos'
    op.create_table(
        'financiamentos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('projeto_id', sa.UUID(), nullable=True),
        sa.Column('evento_id', sa.UUID(), nullable=True),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('fonte', sa.String(), nullable=True),
        sa.Column('agencia', sa.String(), nullable=True),
        sa.Column('edital', sa.String(), nullable=True),
        sa.Column('numero_processo', sa.String(), nullable=True),
        sa.Column('valor_solicitado', sa.Float(), nullable=True),
        sa.Column('valor_aprovado', sa.Float(), nullable=True),
        sa.Column('valor_executado', sa.Float(), nullable=True),
        sa.Column('ano', sa.Integer(), nullable=True),
        sa.Column('vigencia_inicio', sa.Date(), nullable=True),
        sa.Column('vigencia_fim', sa.Date(), nullable=True),
        sa.Column('situacao', sa.String(), nullable=True),
        sa.Column('fonte_dado', sa.String(), nullable=False),
        sa.Column('confianca', sa.String(), nullable=True),
        sa.Column('trecho_original', sa.Text(), nullable=True),
        sa.Column('status_validacao', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evento_id'], ['eventos.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_financiamentos_ano', 'financiamentos', ['ano'], unique=False)
    op.create_index('ix_financiamentos_evento_id', 'financiamentos', ['evento_id'], unique=False)
    op.create_index('ix_financiamentos_id', 'financiamentos', ['id'], unique=False)
    op.create_index('ix_financiamentos_numero_processo', 'financiamentos', ['numero_processo'], unique=False)
    op.create_index('ix_financiamentos_professor_id', 'financiamentos', ['professor_id'], unique=False)
    op.create_index('ix_financiamentos_projeto_id', 'financiamentos', ['projeto_id'], unique=False)
    op.create_index('ix_financiamentos_status_validacao', 'financiamentos', ['status_validacao'], unique=False)
    op.create_index('ix_financiamentos_tipo', 'financiamentos', ['tipo'], unique=False)

    # 11. Create table 'relatorios_projeto'
    op.create_table(
        'relatorios_projeto',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('linha_pesquisa_id', sa.UUID(), nullable=True),
        sa.Column('periodo_inicio', sa.Date(), nullable=True),
        sa.Column('periodo_fim', sa.Date(), nullable=True),
        sa.Column('situacao', sa.String(), nullable=True),
        sa.Column('resumo', sa.Text(), nullable=True),
        sa.Column('participantes', sa.String(), nullable=True),
        sa.Column('alunos_envolvidos', sa.String(), nullable=True),
        sa.Column('instituicoes_parceiras', sa.String(), nullable=True),
        sa.Column('houve_financiamento', sa.Boolean(), nullable=False),
        sa.Column('fonte_financiamento', sa.String(), nullable=True),
        sa.Column('agencia', sa.String(), nullable=True),
        sa.Column('edital', sa.String(), nullable=True),
        sa.Column('numero_processo', sa.String(), nullable=True),
        sa.Column('tipo_recurso', sa.String(), nullable=True),
        sa.Column('valor_solicitado', sa.Float(), nullable=True),
        sa.Column('valor_aprovado', sa.Float(), nullable=True),
        sa.Column('valor_executado', sa.Float(), nullable=True),
        sa.Column('vigencia_inicio', sa.Date(), nullable=True),
        sa.Column('vigencia_fim', sa.Date(), nullable=True),
        sa.Column('situacao_financeira', sa.String(), nullable=True),
        sa.Column('resultados', sa.Text(), nullable=True),
        sa.Column('impacto_social', sa.Text(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['linha_pesquisa_id'], ['linhas_pesquisa.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_relatorios_projeto_id', 'relatorios_projeto', ['id'], unique=False)
    op.create_index('ix_relatorios_projeto_linha_pesquisa_id', 'relatorios_projeto', ['linha_pesquisa_id'], unique=False)
    op.create_index('ix_relatorios_projeto_professor_id', 'relatorios_projeto', ['professor_id'], unique=False)
    op.create_index('ix_relatorios_projeto_tipo', 'relatorios_projeto', ['tipo'], unique=False)
    op.create_index('ix_relatorios_projeto_titulo', 'relatorios_projeto', ['titulo'], unique=False)

    # 12. Create table 'anexos'
    op.create_table(
        'anexos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('relatorio_projeto_id', sa.UUID(), nullable=True),
        sa.Column('financiamento_id', sa.UUID(), nullable=True),
        sa.Column('projeto_id', sa.UUID(), nullable=True),
        sa.Column('evento_id', sa.UUID(), nullable=True),
        sa.Column('tipo_anexo', sa.String(), nullable=False),
        sa.Column('arquivo_url', sa.String(), nullable=False),
        sa.Column('arquivo_nome', sa.String(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evento_id'], ['eventos.id'], ),
        sa.ForeignKeyConstraint(['financiamento_id'], ['financiamentos.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['relatorio_projeto_id'], ['relatorios_projeto.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_anexos_evento_id', 'anexos', ['evento_id'], unique=False)
    op.create_index('ix_anexos_financiamento_id', 'anexos', ['financiamento_id'], unique=False)
    op.create_index('ix_anexos_id', 'anexos', ['id'], unique=False)
    op.create_index('ix_anexos_professor_id', 'anexos', ['professor_id'], unique=False)
    op.create_index('ix_anexos_projeto_id', 'anexos', ['projeto_id'], unique=False)
    op.create_index('ix_anexos_relatorio_projeto_id', 'anexos', ['relatorio_projeto_id'], unique=False)

    # 13. Create table 'alertas_lacunas'
    op.create_table(
        'alertas_lacunas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('professor_id', sa.UUID(), nullable=False),
        sa.Column('curriculo_upload_id', sa.UUID(), nullable=True),
        sa.Column('tipo_lacuna', sa.String(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=False),
        sa.Column('gravidade', sa.String(), nullable=False),
        sa.Column('acao_recomendada', sa.String(), nullable=True),
        sa.Column('resolvido', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['curriculo_upload_id'], ['curriculo_uploads.id'], ),
        sa.ForeignKeyConstraint(['professor_id'], ['professores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alertas_lacunas_curriculo_upload_id', 'alertas_lacunas', ['curriculo_upload_id'], unique=False)
    op.create_index('ix_alertas_lacunas_id', 'alertas_lacunas', ['id'], unique=False)
    op.create_index('ix_alertas_lacunas_professor_id', 'alertas_lacunas', ['professor_id'], unique=False)
    op.create_index('ix_alertas_lacunas_resolvido', 'alertas_lacunas', ['resolvido'], unique=False)
    op.create_index('ix_alertas_lacunas_tipo_lacuna', 'alertas_lacunas', ['tipo_lacuna'], unique=False)

    # 14. Create table 'logs_validacao'
    op.create_table(
        'logs_validacao',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('entidade', sa.String(), nullable=False),
        sa.Column('entidade_id', sa.UUID(), nullable=False),
        sa.Column('acao', sa.String(), nullable=False),
        sa.Column('valor_anterior', sa.String(), nullable=True),
        sa.Column('valor_novo', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_logs_validacao_entidade', 'logs_validacao', ['entidade'], unique=False)
    op.create_index('ix_logs_validacao_entidade_id', 'logs_validacao', ['entidade_id'], unique=False)
    op.create_index('ix_logs_validacao_id', 'logs_validacao', ['id'], unique=False)
    op.create_index('ix_logs_validacao_user_id', 'logs_validacao', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('logs_validacao')
    op.drop_table('alertas_lacunas')
    op.drop_table('anexos')
    op.drop_table('relatorios_projeto')
    op.drop_table('financiamentos')
    op.drop_table('producoes')
    op.drop_table('eventos')
    op.drop_table('projetos')
    op.drop_table('pdf_sections')
    op.drop_table('pdf_pages')
    op.drop_table('curriculo_uploads')
    op.drop_table('professores')
    op.drop_table('linhas_pesquisa')
    op.drop_table('users')
