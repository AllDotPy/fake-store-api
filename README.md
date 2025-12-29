
# Fake Store

A simple basic store management system API built with Django Rest Framework (DRF) for the FletX showcase at PyCon Togo 2025.

## Description

Fake Store is a demonstration project designed to showcase the capabilities of the FletX framework. This API serves as the backend for an e-commerce application developed specifically for the FletX showcase at PyCon Togo 2025. It provides a straightforward and effective solution for managing products, orders, and users, highlighting the integration and efficiency of FletX in developing full-stack applications.

## Features

- Product Management: Add, modify, delete, and view products.
- Order Management: Create, view, and track orders.
- User Management: Register, authenticate, and manage user profiles.
- Intuitive and well-documented API interface.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.11 or higher
- Django 5.2.4 or higher
- Django Rest Framework
- uv (recommended for dependency management)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/AllDotPy/fake-store-api.git
cd fake-store
```

2. Create a virtual environment and activate it:

```bash
uv venv --python 3.11
source venv/bin/activate  # On Linux/Mac
venv\Scripts\activate  # On Windows
```

3. Install dependencies with uv:

```bash
uv sync
```

4. Set up the database:

```bash
python manage.py migrate
```

5. Create a super user
```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

## Usage

Once the server is running, you can access the API at the following URL: `http://localhost:8000/`.

Refer to the API documentation for more details on available endpoints and their usage.

## popuulating the database

to create generic products with categories run:
```bash
python manage.py populate
# this will create 100 products use -l to specify the number of products.
```

## Contributing

Contributions are welcome! To contribute to this project, follow these steps:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any questions or suggestions, feel free to contact us at: contact@fletx.com
```

Feel free to customize this template according to the specifics of your project and any additional information you want to include.
