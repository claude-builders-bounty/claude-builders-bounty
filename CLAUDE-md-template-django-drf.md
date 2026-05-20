# CLAUDE.md Template: Django + DRF + PostgreSQL

> Optimized for AI-assisted development with Claude Code

## Project Overview

This is a [Django](https://www.djangoproject.com/) project with Django REST Framework (DRF) and PostgreSQL.

## Tech Stack

- **Framework**: Django 5.0+
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Testing**: pytest + pytest-django
- **Linting**: ruff + black

## Project Structure

```
project/
├── config/           # Project settings
│   ├── settings/     # Split settings
│   ├── urls.py
│   └── wsgi.py
├── apps/             # Django apps
│   ├── users/
│   ├── core/
│   └── api/
├── manage.py
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```

## AI Assistant Guidelines

### Model Pattern

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model with additional fields."""
    
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self) -> str:
        return self.username
```

### Serializer Pattern

```python
# apps/users/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio', 'avatar']
        read_only_fields = ['id']
    
    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value
```

### ViewSet Pattern

```python
# apps/users/views.py
from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User CRUD operations."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by search query
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(username__icontains=search)
        return queryset
```

### URL Pattern

```python
# apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

### Test Pattern

```python
# apps/users/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from ..models import User

@pytest.mark.django_db
class TestUserViewSet:
    """Tests for UserViewSet."""
    
    def test_list_users(self):
        """Test listing users."""
        User.objects.create_user(username='test', email='test@example.com')
        
        client = APIClient()
        response = client.get(reverse('user-list'))
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
    
    def test_create_user(self):
        """Test creating a user."""
        client = APIClient()
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123'
        }
        
        response = client.post(reverse('user-list'), data)
        
        assert response.status_code == 201
        assert User.objects.filter(username='newuser').exists()
```

## Common Tasks

### Add a new app

```bash
python manage.py startapp apps/newapp
```

### Create migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Run tests

```bash
pytest
pytest --cov=apps
```

### Create superuser

```bash
python manage.py createsuperuser
```

## Performance

- Use `select_related()` for foreign keys
- Use `prefetch_related()` for many-to-many
- Add database indexes: `db_index=True`
- Use caching: Django's cache framework

## Security

- Use environment variables for secrets
- Enable CSRF protection
- Use HTTPS in production
- Keep dependencies updated

---

**Built with Claude Code** 🤖
