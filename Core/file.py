from os import getenv
from uuid import uuid4

from boto3 import client

from fastapi import UploadFile


class Files:
    def __init__(self):
        self.ENDPOINT_URL = getenv("S3_ENDPOINT_URL")
        self.ACCESS_KEY = getenv("S3_ACCESS_KEY")
        self.SECRET_KEY = getenv("S3_SECRET_KEY")
        self.BUCKET_NAME = getenv("S3_BUCKET_NAME")
        self.client = s3_client = client("s3",
                                         endpoint_url=self.ENDPOINT_URL,
                                         aws_access_key_id=self.ACCESS_KEY,
                                         aws_secret_access_key=self.SECRET_KEY)

    def upload(self, file: UploadFile, name: str) -> None:
        self.client.upload_fileobj(file.file, Bucket=self.BUCKET_NAME, Key=name,ExtraArgs={
            'ContentType': file.content_type,
            'ACL': 'public-read'
        })

    def delete(self):
        pass
    def url(self):
        return f"{self.ENDPOINT_URL}/{self.BUCKET_NAME}/"

    def safe_name(self, file: UploadFile) -> str:
        exp = file.filename.split(".")[-1]
        name = uuid4()
        return f"{name}.{exp}"
