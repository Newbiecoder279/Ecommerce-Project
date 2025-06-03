# Ecommerce-Project
A simple Django-based product catalog web application with category filtering and responsive Tailwind CSS styling. Users can browse products, view by category, and access detailed product pages.

# 🛍️ Django Product Catalog

A simple Django web application for displaying products with category-based filtering. Styled using Tailwind CSS for a clean, responsive UI.

---

## ✨ Features

- 📂 **Categories Sidebar** — Filter products by category
- 🛒 **Product Listings** — View product details including name, image, description, and price
- 🖼️ **Image Handling** — Product images with fallback message when not available
- 🎨 **Tailwind CSS Styling** — Fully responsive and minimal UI
- 🔗 **Dynamic Routing** — Clean, SEO-friendly URLs for categories and product details

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Django 4.x or later
- Tailwind CSS (can be set up with `django-tailwind` or CDN)

---

### 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/django-product-catalog.git
cd django-product-catalog

# Create a virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Run the server
python manage.py runserver

Adding Product Images
Make sure your MEDIA_URL and MEDIA_ROOT are correctly configured in settings.py:
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

and update urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your other URL patterns
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

🛠️ Tech Stack
Backend: Django

Frontend: Tailwind CSS

Database: SQLite (default), easily switchable to PostgreSQL or MySQL

Templating: Django Templates



