from fastapi import FastAPI

from backend.routers import announcement, auth, category, users

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(announcement.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}
