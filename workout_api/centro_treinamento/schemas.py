from typing import Annotated

from pydantic import Field
from workout_api.contrib.schemas import BaseSchema


class CentroTreinamento(BaseSchema):
    nome: Annotated[str, Field(description='Nome do centro de treinamento', example='CT King', max_length=20)]
    endereco: Annotated[str, Field(description='Endereço do centro de treinamento', example='Rua Artur Antunes 1981', max_length=60)]
    proprietario: Annotated[str, Field(description='Proprietário do centro de treinamento', example='Gabriel', max_length=30)]
    
