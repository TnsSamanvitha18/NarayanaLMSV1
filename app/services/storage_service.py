import os
from flask import current_app

class StorageService:
    """
    Storage Service: Handles file uploads/retrievals locally or S3-compatibly (MinIO/AWS S3).
    """

    @staticmethod
    def get_s3_client():
        import boto3
        return boto3.client(
            's3',
            aws_access_key_id=current_app.config.get('S3_ACCESS_KEY'),
            aws_secret_access_key=current_app.config.get('S3_SECRET_KEY'),
            endpoint_url=current_app.config.get('S3_ENDPOINT_URL')  # Supports self-hosted MinIO!
        )

    @staticmethod
    def upload_file(file_obj, filename, folder='materials'):
        """
        Upload file locally or to S3/MinIO bucket.
        """
        provider = current_app.config.get('STORAGE_PROVIDER', 'local')
        
        if provider == 's3':
            s3 = StorageService.get_s3_client()
            bucket = current_app.config.get('S3_BUCKET')
            key = f"{folder}/{filename}"
            
            # Reset seek pointer to start of file
            file_obj.seek(0)
            s3.upload_fileobj(file_obj, bucket, key)
            return f"s3://{bucket}/{key}"
        else:
            # Fallback to local storage
            upload_dir = os.path.join(current_app.root_path, '..', 'uploads', folder)
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file_obj.save(filepath)
            return filepath

    @staticmethod
    def download_file(filename, folder='materials'):
        """
        Stream/Read file content from S3/MinIO or local filesystem.
        """
        provider = current_app.config.get('STORAGE_PROVIDER', 'local')
        
        if provider == 's3':
            import io
            s3 = StorageService.get_s3_client()
            bucket = current_app.config.get('S3_BUCKET')
            key = f"{folder}/{filename}"
            
            buffer = io.BytesIO()
            s3.download_fileobj(bucket, key, buffer)
            buffer.seek(0)
            return buffer
        else:
            upload_dir = os.path.join(current_app.root_path, '..', 'uploads', folder)
            filepath = os.path.join(upload_dir, filename)
            return open(filepath, 'rb')
