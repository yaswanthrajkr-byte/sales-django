# Spare Parts Management System

A simple Django project to manage spare parts, dealers, and orders.

## Features

* Add and manage products with prices.
* Add and manage dealers.
* Place and track orders.
* View inventory.

## Requirements

* Python 3.10 or higher
* Django 5.x
* Django REST Framework
* SQLite (default) or any other database

## Environment Variables

Create a .env file in the project root directory with the following variables:

SECRET_KEY=your-secret-key  
DEBUG=True

These variables are required to run this Django application.

## Installation

1. Clone the project:

```
git clone <repo-url>
```

2. Navigate to project folder:

```
cd <project-folder>
```

3. Create and activate a virtual environment:

```
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:

```
pip install -r requirements.txt
```

5. Apply migrations:

```
python manage.py makemigrations
python manage.py migrate
```

6. Create superuser (admin):

```
python manage.py createsuperuser
```

7. Run the development server:

```
python manage.py runserver
```

## Usage

* Open `http://127.0.0.1:8000/admin` to manage products, dealers, orders, and inventory.
* Use Django shell for testing data:

```
python manage.py shell
```

## Notes

* Make sure virtual environment is activated before running server or migrations.
* You can use `python manage.py runserver 0.0.0.0:8000` to make the server accessible on local network for demo purposes.