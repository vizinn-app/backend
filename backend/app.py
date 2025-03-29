from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_session
from backend.models import User
from backend.schemas import LoginSchema, Message, UserList, UserPublic, UserSchema
from backend.security import get_password_hash, verify_password

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
        senha=get_password_hash(user.senha),
        email=user.email,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@app.get('/users/', response_model=UserList)
def read_users(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    users = session.scalars(select(User).offset(skip).limit(limit)).all()
    return {'users': users}


@app.get('/user/{user_id}', response_model=UserPublic)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.scalars(select(User).where(User.id == user_id)).first()
    return user


@app.delete('/users/{user_id}', response_model=Message)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    db_user = session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='User not found')

    session.delete(db_user)
    session.commit()

    return {'message': 'User deleted'}


@app.post('/login/', response_model=UserPublic)
def login(user: LoginSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(select(User).where((User.email == user.email)))

    if not db_user or not verify_password(user.senha, db_user.senha):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Invalid email or password'
        )

    return db_user
