from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, status
from fastapi_pagination import Page, paginate
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from workout_api.atleta.models import AtletaModel
from workout_api.atleta.schemas import AtletaGetAll, AtletaIn,  AtletaOut, AtletaUpdate
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency

router = APIRouter()


@router.post(
    path='/',
    summary='Criar um novo atleta',
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut,
)
async def post(
    db_session: DatabaseDependency, atleta_in: AtletaIn = Body(...)
) -> AtletaOut:
    categoria_nome = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinamento.nome

    categoria = (
        (
            await db_session.execute(
                select(CategoriaModel).filter_by(nome=categoria_nome)
            )
        )
        .scalars()
        .first()
    )

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'A categoria {categoria_nome} não foi encontrada.',
        )

    centro_treinamento = (
        (
            await db_session.execute(
                select(CentroTreinamentoModel).filter_by(
                    nome=centro_treinamento_nome
                )
            )
        )
        .scalars()
        .first()
    )

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'O Centro de treinamento {centro_treinamento_nome} não foi encontrada.',
        )

    try:
        atleta_out = AtletaOut(
            id=uuid4(),
            created_at=datetime.now(timezone.utc),
            **atleta_in.model_dump(),
        )
        atleta_model = AtletaModel(
            **atleta_out.model_dump(
                exclude={'categoria', 'centro_treinamento'}
            )
        )
        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f'Já existe um atleta cadastrado com esse CPF.'
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ocorreu um erro ao inserir os dados no banco',
        )

    return atleta_out


@router.get(
    path='/',
    summary='Consultar todos os Atletas',
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaGetAll],
)
async def query_all(db_session: DatabaseDependency, nome: str | None = None, cpf: str | None = None) -> list[AtletaOut]:
    atletas: list[AtletaGetAll] = (
        (await db_session.execute(select(AtletaModel))).scalars().all()
    )
    
    results = [AtletaGetAll.model_validate(atleta) for atleta in atletas if (nome is None and cpf is None) or (nome == atleta.nome or cpf == atleta.cpf)]
    return paginate(results)


@router.get(
    path='/{id}',
    summary='Consultar um Atleta pelo id',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query_by_id(id: UUID4, db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = (
        (await db_session.execute(select(AtletaModel).filter_by(id=id)))
        .scalars()
        .first()
    )

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada no id: {id}',
        )

    return atleta


@router.patch(
    path='/{id}',
    summary='Editar um Atleta pelo id',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def patch_by_id(
    id: UUID4,
    db_session: DatabaseDependency,
    atleta_up: AtletaUpdate = Body(...),
) -> AtletaOut:

    atleta: AtletaOut = (
        (await db_session.execute(select(AtletaModel).filter_by(id=id)))
        .scalars()
        .first()
    )

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada no id: {id}',
        )

    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta


@router.delete(
    path='/{id}',
    summary='Deletar um Atleta pelo id',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_by_id(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta: AtletaOut = (
        (await db_session.execute(select(AtletaModel).filter_by(id=id)))
        .scalars()
        .first()
    )

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Atleta não encontrada no id: {id}',
        )

    await db_session.delete(atleta)
    await db_session.commit()
