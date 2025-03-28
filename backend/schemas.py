from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    nome: str
    cpf: str
    telefone: str
    senha: str
    email: EmailStr


class UserPublic(BaseModel):
    id: int
    nome: str
    cpf: str
    telefone: str
    email: EmailStr


class UserDB(UserSchema):
    id: int


class UserList(BaseModel):
    users: list[UserPublic]


class Message(BaseModel):
    message: str
