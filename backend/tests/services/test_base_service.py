import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict
from typing import Union, Optional
import firebase_admin
from firebase_admin import credentials, auth, firestore

from services.base_service import BaseService
from utils import get_token

# Test model for concrete implementation
class TestModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
    
    id: Optional[str] = Field(None, exclude=True)
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Concrete implementation of BaseService for testing
class TestService(BaseService):
    @property
    def collection(self):
        return "test_collection"

    def __init__(self):
        super().__init__()
        self._model_class = TestModel

@pytest.fixture(autouse=True)
def setup_firebase():
    """Initialize Firebase app for testing."""
    cred = Mock(spec=credentials.Certificate)
    app = Mock()
    app.name = '[DEFAULT]'
    
    with patch('firebase_admin.initialize_app', return_value=app) as mock_init, \
         patch('firebase_admin.get_app', return_value=app) as mock_get_app, \
         patch('firebase_admin.delete_app') as mock_delete:
        mock_init.return_value = app
        firebase_admin.initialize_app(cred)
        yield app
        firebase_admin.delete_app(app)

@pytest.fixture
def mock_auth():
    """Mock Firebase Auth."""
    with patch('firebase_admin.auth') as mock:
        # Create a dict for verify_id_token to return
        mock.verify_id_token.return_value = {
            'uid': 'test_user_id',
            'email': 'test@example.com'
        }
        yield mock

@pytest.fixture
def mock_firestore():
    """Mock Firestore client and its operations."""
    test_data = {
        'name': 'Test Item',
        'description': 'Test Description',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    # Create mock document snapshot
    mock_snapshot = Mock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = test_data
    
    # Create mock document reference with async operations
    mock_doc = Mock()
    mock_doc.get = Mock(return_value=mock_snapshot)
    mock_doc.set = AsyncMock()
    mock_doc.update = AsyncMock()
    mock_doc.delete = AsyncMock()
    
    # Create mock collection reference
    mock_collection = Mock()
    mock_collection.document.return_value = mock_doc
    
    # Create mock firestore client
    mock_client = Mock()
    mock_client.collection.return_value = mock_collection
    
    with patch('firebase_admin.firestore.client', return_value=mock_client):
        yield mock_client

@pytest.fixture
def mock_get_token():
    """Mock get_token function."""
    with patch('utils.get_token') as mock:
        mock.return_value = "test_token"
        yield mock

@pytest.fixture
def service(mock_firestore):
    """Service fixture with mocked dependencies."""
    return TestService()

@pytest.fixture
def test_request():
    request = Mock(spec=Request)
    request.headers = {"Authorization": "Bearer test_token"}
    return request

@pytest.mark.asyncio
async def test_verify_user_success(service, test_request, mock_auth, mock_get_token):
    user_id = service.verify_user(test_request)
    assert user_id == "test_user_id"
    mock_auth.verify_id_token.assert_called_once_with("test_token")

@pytest.mark.asyncio
async def test_verify_user_invalid_token(service, test_request, mock_auth, mock_get_token):
    mock_auth.verify_id_token.side_effect = auth.InvalidIdTokenError("Invalid token")
    
    with pytest.raises(HTTPException) as exc:
        service.verify_user(test_request)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_verify_user_no_token(service):
    request = Mock(spec=Request)
    request.headers = {}
    
    with pytest.raises(HTTPException) as exc:
        service.verify_user(request)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_create_success(service, test_request):
    data = TestModel(name="New Item", description="New Description")
    result = await service.create(test_request, data)
    assert isinstance(result, TestModel)
    assert result.name == "Test Item"

@pytest.mark.asyncio
async def test_get_success(service, test_request):
    result = await service.get(test_request, "test_id")
    assert isinstance(result, TestModel)
    assert result.name == "Test Item"
    assert result.description == "Test Description"

@pytest.mark.asyncio
async def test_update_success(service, test_request):
    update_data = TestModel(name="Updated Item", description="Updated Description")
    result = await service.update(test_request, "test_id", update_data)
    assert isinstance(result, TestModel)
    assert result.name == "Test Item"

@pytest.mark.asyncio
async def test_delete_success(service, test_request):
    await service.delete("test_id")
