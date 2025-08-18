
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

- Python 3.8 or higher
- Django 3.2 or higher
- Django Rest Framework
- uv (recommended for dependency management)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/fake-store.git
cd fake-store
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
venv\Scripts\activate  # On Windows
```

3. Install dependencies with uv:

```bash
pip install uv
uv pip install -r requirements.txt
```

4. Set up the database:

```bash
python manage.py migrate
```

5. Run the development server:

```bash
python manage.py runserver
```

## Usage

Once the server is running, you can access the API at the following URL: `http://localhost:8000/api/`.

Refer to the API documentation for more details on available endpoints and their usage.

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