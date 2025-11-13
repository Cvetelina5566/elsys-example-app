import os
import io
import pytest
from fastapi.testclient import TestClient
from main import app,STORAGE_DIR

client=TestClient(app)

@pytest.fixture(autouse=True)
def clean_storage():
    for f in STORAGE_DIR.iterdir():
        if f.is_file():
            f.unlink()
    yield
    for f in STORAGE_DIR.iterdir():
        if f.is_file():
            f.unlink()


def test_root_endpoint():
    response=client.get("/")
    assert response.status_code==200
    data = response.json()
    assert "message" in data
    assert data["message"] == "File Storage API"
    assert any("/files"in ep for ep in data["endpoints"])


def test_store_file_success():
    file_content=b"Hello, world!"
    response=client.post(
        "/files",
        files={"file":("test.txt",io.BytesIO(file_content),"text/plain")},
    )
    assert response.status_code==200
    data=response.json()
    assert data["message"] == "File stored successfully"
    assert data["filename"] == "test.txt"
    assert data["size"] == len(file_content)

    assert (STORAGE_DIR / "test.txt").exists()


def test_get_file_success():
    file_path = STORAGE_DIR / "sample.txt"
    file_path.write_text("data")
    response = client.get("/files/sample.txt")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment")


def test_get_file_not_found():
    response = client.get("/files/missing.txt")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_files_and_metrics():
    client.post("/files",files={"file":("a.txt",io.BytesIO(b"aaa"),"text/plain")})
    client.post("/files",files={"file": ("b.txt", io.BytesIO(b"bbb"), "text.plain")})

    response=client.get("/files")
    assert response.status_code==200
    data=response.json()
    assert set(data["files"])=={"a.txt","b.txt"}
    assert data["count"]==2

    metrics_resp=client.get("/metrics")
    metrics=metrics_resp.json()
    assert metrics_resp.status_code==200
    assert "files_stored_total" in metrics
    assert metrics["files_current"]==2
    assert metrics["total_storage_bytes"]>0
    assert "timestamp" in metrics


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "service" in data
