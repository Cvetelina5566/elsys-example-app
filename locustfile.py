from locust import HttpUser, task, between
import io

class FileStorageUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(1)
    def list_files(self):
        self.client.get("/files")
    
    @task(1)
    def upload_file(self):
        file_content = io.BytesIO(b"Sample file content")
        files={"file": ("test_locust.txt",file_content,"text/plain")}
        self.client.post("/files", files=files)

    @task(2)
    def root_endpoint(self):
        self.client.get("/")
    
    @task(3)
    def health_check(self):
        self.client.get("/health")