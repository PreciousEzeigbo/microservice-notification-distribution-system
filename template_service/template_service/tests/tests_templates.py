import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from templates.models import EmailTemplate


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_template():
    return EmailTemplate.objects.create(
        name='test_template',
        template_type='notification',
        subject='Test {{variable}}',
        html_content='<p>Hello {{user.name}}</p>',
        description='Test template'
    )


@pytest.mark.django_db
class TestEmailTemplateAPI:
    
    def test_create_template(self, api_client):
        """Test creating a new template"""
        url = reverse('templates_app:template-list')
        data = {
            'name': 'new_template',
            'template_type': 'welcome',
            'subject': 'Welcome {{name}}',
            'html_content': '<h1>Hello {{name}}</h1>',
            'description': 'New template'
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'new_template'
    
    def test_get_template(self, api_client, sample_template):
        """Test retrieving a template"""
        url = reverse('templates_app:template-detail', kwargs={'name': sample_template.name})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == sample_template.name
    
    def test_validate_template(self, api_client, sample_template):
        """Test template validation with variables"""
        url = reverse('templates_app:template-validate', kwargs={'name': sample_template.name})
        data = {
            'variables': {
                'variable': 'test',
                'user': {'name': 'John'}
            }
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
    
    def test_extract_placeholders(self, api_client, sample_template):
        """Test extracting placeholders from template"""
        url = reverse('templates_app:template-placeholders', kwargs={'name': sample_template.name})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'placeholders' in response.data
        assert 'user.name' in response.data['placeholders']
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        url = reverse('templates_app:template-health')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'