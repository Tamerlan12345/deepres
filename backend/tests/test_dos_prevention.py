import pytest
from pydantic import ValidationError
from app.api import UserLogin, ReportCreate

def test_user_login_max_length_username():
    with pytest.raises(ValidationError) as exc_info:
        UserLogin(username="a" * 51, password="password")

    assert "String should have at most 50 characters" in str(exc_info.value)

def test_user_login_max_length_password():
    with pytest.raises(ValidationError) as exc_info:
        UserLogin(username="username", password="a" * 129)

    assert "String should have at most 128 characters" in str(exc_info.value)

def test_report_create_max_length_query():
    with pytest.raises(ValidationError) as exc_info:
        ReportCreate(query="a" * 2001)

    assert "String should have at most 2000 characters" in str(exc_info.value)

def test_user_login_valid():
    user = UserLogin(username="a" * 50, password="a" * 128)
    assert user.username == "a" * 50
    assert user.password == "a" * 128

def test_report_create_valid():
    report = ReportCreate(query="a" * 2000)
    assert report.query == "a" * 2000
