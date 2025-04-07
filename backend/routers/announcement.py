from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_session
from backend.models import User
from backend.security import get_current_user

router = APIRouter(prefix='/announcement', tags=['announcement'])
T_Session = Annotated[Session, Depends(get_session)]
T_User = Annotated[User, Depends(get_current_user)]
