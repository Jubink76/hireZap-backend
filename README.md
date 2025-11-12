# 🚀 hireZap - Backend
HireZap backend provides the **REST API** and real-time infrastructure powering the platform.  
It is built with **Django REST Framework** following **Clean Architecture** principles.
## 📚 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Modules](#modules)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features
- 🧑‍💼 **Recruiters** can post jobs & schedule multi-stage interviews.
- 👤 **Candidates** can apply & attend interviews with integrated coding compiler.
- 🛡️ **Admin** handles verification, subscriptions, and user management.
- 🔐 JWT Authentication + HttpOnly cookies for secure sessions.
- ☁️ Cloudinary for user profile images.
- 🔑 OAuth with Google, GitHub, LinkedIn (coming soon).
- ⚡ Redis used for OTP.
- 📦 PostgreSQL for data persistence.
- 🌀 Celery (planned) for background tasks & automation.
- 🎥 WebRTC (planned) for live interviews.

## 🛠 Tech Stack

| Technology | Description |
|------------|-------------|
| [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) | Programming language |
| [![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/) | Core framework |
| [![Django REST Framework](https://img.shields.io/badge/Django_REST-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/) | REST API |
| [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/) | Database |
| [![Redis](https://img.shields.io/badge/Redis-D82C20?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/) | Caching & OTP |
| [![Cloudinary](https://img.shields.io/badge/Cloudinary-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white)](https://cloudinary.com/) | Media storage |
| [![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)](https://jwt.io/) | Authentication (JWT + HttpOnly Cookies) |
| [![Clean Architecture](https://img.shields.io/badge/Clean_Architecture-007ACC?style=for-the-badge)](https://medium.com/@peter.shen_53785/clean-architecture-1e9f4c6a5f38) | Project structure |

## 🗂 Modules
- Candidate API
- Recruiter API
- Admin API

---

## 💻 Installation

Clone the repository:

```bash
git clone https://github.com/Jubink76/hirezap-backend.git
cd hirezap-backend
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

## Env
- SECRET_KEY="your secret key
- DEBUG=True
- DB_ENGINE=django.db.backends.postgresql
- DB_NAME=db_name
- DB_USER=db_user
- DB_PASSWORD=password
- DB_HOST=localhost
- DB_PORT=5432

# email 
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_HOST_USER=host@gmail.com
- EMAIL_HOST_PASSWORD=password_key
- EMAIL_USE_TLS=True
- EMAIL_USE_SSL=True
- DEFAULT_FROM_EMAIL=sender@gmail.com

# redis
- REDIS_HOST=127.0.0.1
- REDIS_PORT=6379
- REDIS_DB=0

## usage
```bash
python manage.py runserver
```
