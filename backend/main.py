from fastapi import FastAPI

from backend.books.router import router as books_router


app = FastAPI(title='BD for books')


@app.get('/', summary='Главная страница')
async def main_page():
    return {'message': 'Главная страница'}


@app.get('/api/ping', summary='Healthcheck')
async def healthcheck():
    return {'status': 'ok'}


app.include_router(books_router, prefix='/api/v1')
