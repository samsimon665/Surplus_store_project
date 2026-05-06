# Surplus Store Project

A Django-based e-commerce platform for surplus clothing management and online shopping.

---

## Features

- User authentication
- Product catalog
- Category & subcategory management
- Shopping cart
- Wishlist
- Razorpay payment integration
- Order management
- Coupon system
- Notifications
- Admin dashboard
- Analytics dashboard

---

## Tech Stack

- Python
- Django
- SQLite (currently)
- HTML/CSS/JavaScript
- Bootstrap
- Razorpay
- Celery
- Redis

---

## Installation

Clone the repository:

```bash
git clone <repo-url>
```

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

### Windows
```bash
venv\Scripts\activate
```

### Linux/Mac
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Run server:

```bash
python manage.py runserver
```

---

## Environment Variables

Create a `.env` file and add required environment variables.

Example:

```env
SECRET_KEY=your_secret_key
DEBUG=True
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret
```

---

## Project Status

Currently under active development and production deployment preparation.
