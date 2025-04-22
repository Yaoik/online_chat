## Getting started

1. Создайте файл `.env` в корневой директории проекта
```bash
cp .env.template .env
```
2. Запустите приложение
```bash
docker-compose up
```
3. Выполните миграцию базы данных
```bash
docker-compose exec django python manage.py migrate
```
4. Cоздайте администратора
```bash
docker-compose exec django python manage.py createsuperuser
```
5. Соберите статику
```bash
docker-compose exec django python manage.py collectstatic
```
6. Выполните тесты
```bash
docker-compose exec django pytest
```
7. Некоторые полезные страницы
   * Админка - http://localhost:8000/admin/
   * API документация
     * Swagger - http://localhost:8000/api/schema/swagger-ui/
     * Redoc - http://localhost:8000/api/schema/redoc/
