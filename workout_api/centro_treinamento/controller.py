from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, status
from fastapi_pagination import Page, paginate
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.centro_treinamento.schemas import (
    CentroTreinamentoIn,
    CentroTreinamentoOut,
)
from workout_api.contrib.dependencies import DatabaseDependency

router = APIRouter()


@router.post(
    path='/',
    summary='Cria um novo Centro de treinamento',
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut,
)
async def post(
    db_session: DatabaseDependency,
    centro_treinamento_in: CentroTreinamentoIn = Body(...),
) -> CentroTreinamentoOut:

    try:
        centro_treinamento_out = CentroTreinamentoOut(
            id=uuid4(), **centro_treinamento_in.model_dump()
        )
        centro_treinamento_model = CentroTreinamentoModel(
            **centro_treinamento_out.model_dump()
        )

        db_session.add(centro_treinamento_model)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f'Já existe um Centro de Treinamento cadastrado com esse nome.'
        )
        
    return centro_treinamento_out


@router.get(
    path='/',
    summary='Consultar todos os Centros de treinamento',
    status_code=status.HTTP_200_OK,
    response_model=Page[CentroTreinamentoOut],
)
async def query(db_session: DatabaseDependency) -> list[CentroTreinamentoOut]:
    categorias: list[CentroTreinamentoOut] = (
        (await db_session.execute(select(CentroTreinamentoModel)))
        .scalars()
        .all()
    )

    return paginate(categorias)


@router.get(
    path='/{id}',
    summary='Consultar um Centro de treinamento pelo id',
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut,
)
async def query_by_id(
    id: UUID4, db_session: DatabaseDependency
) -> CentroTreinamentoOut:
    categoria: CentroTreinamentoOut = (
        (
            await db_session.execute(
                select(CentroTreinamentoModel).filter_by(id=id)
            )
        )
        .scalars()
        .first()
    )

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Centro de treinamento não encontrada no id: {id}',
        )

    return categoria
