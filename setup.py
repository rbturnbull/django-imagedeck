from setuptools import setup

requirements = [
    "Django>3",
    "django-imagekit>=4.0.2",
    "django-polymorphic>=3.0.0",
    "django-filer>=2.0.2",
    "requests>=2.24.0",
    "django-admin-sortable2>=0.7.6",
    "easy-thumbnails",
]

setup(
    install_requires=requirements,
)