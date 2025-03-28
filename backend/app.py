from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_session
from backend.models import User
from backend.schemas import UserPublic, UserSchema

app = FastAPI()


@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(User).where((User.nome == user.nome) | (User.email == user.email))
    )

    if db_user:
        if db_user.nome == user.nome:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail='Username already registered'
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail='Email already registered'
            )

    db_user = User(
        nome=user.nome,
        cpf=user.cpf,
        telefone=user.telefone,
        senha=user.senha,
        email=user.email,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user
