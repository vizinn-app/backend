import random
from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from twilio.rest import Client
from backend.settings import Settings

from backend.database import get_session
from backend.models import User, UserVerification
from backend.schemas import (
    Message,
    Token,
    UserList,
    UserPublic,
    UserSchema,
    verifyCodeSchema,
)
from backend.security import create_access_token, get_password_hash, verify_password

app = FastAPI()

account_sid = 'AC86990c387fd4133bc6de6657430e3293'
auth_token = 'badf430b8957bd7a1c99caebaed9f158'
twilio_phone_number = '+12394280641'

client = Client(Settings().account_sid, Settings().auth_token)


@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(User).where(
            (User.full_name == user.full_name) | (User.email == user.email)
        )
    )

    if db_user:
        if db_user.full_name == user.full_name:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail='Username already registered'
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail='Email already registered'
            )

    db_user = User(
        full_name=user.full_name,
        cpf=user.cpf,
        phone=user.phone,
        password=get_password_hash(user.password),
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


@app.post('/token/', response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Incorrect email or password'
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Incorrect email or password'
        )

    access_token = create_access_token(data={'sub': user.email})

    verification_code = f'{random.randint(100000, 999999)}'

    user_verification = session.scalar(
        select(UserVerification).where(UserVerification.user_id == user.id)
    )

    if user_verification:
        user_verification.verification_code = verification_code
        user_verification.is_verified = False
    else:
        user_verification = UserVerification(
            user_id=user.id, verification_code=verification_code, is_verified=False
        )
        session.add(user_verification)

    session.commit()

    try:
        client.messages.create(
            body=f'Your verification code is: {verification_code}',
            from_=Settings().twilio_phone_number,
            to=f'+55{user.phone}',
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Failed to send SMS: {str(e)}',
        )

    return {'access_token': access_token, 'token_type': 'bearer'}


@app.post('/verify-code/{user_id}', response_model=Message)
def verify_code(
    user_id: int, data: verifyCodeSchema, session: Session = Depends(get_session)
):
    user_verification = session.scalar(
        select(UserVerification).where(UserVerification.user_id == user_id)
    )

    if not user_verification:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Verification code not found'
        )

    if user_verification.verification_code != data.verification_code:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Invalid verification code'
        )

    user_verification.is_verified = True
    session.commit()

    return {'message': 'Code verified successfully'}
