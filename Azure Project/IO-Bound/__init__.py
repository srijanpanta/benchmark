import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os
import uuid
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('IO-Bound benchmark function processed a request.')

    try:
        # Get connection string from local settings or environment variables
        connect_str = os.getenv('AzureWebJobsStorage')
        if not connect_str:
            return func.HttpResponse("Storage connection string not found.", status_code=500)

        # Get file size from request, default to 1024 KB (1MB)
        req_body = req.get_json()
        file_size_kb = int(req_body.get('file_size_kb', 1024))
    except (ValueError, AttributeError):
        file_size_kb = 1024

    try:
        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "benchmark-container"

        # Create the container if it doesn't exist
        try:
            container_client = blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
        except Exception as e:
            logging.error(f"Container creation failed: {e}")
            # Continue, as it might exist already; upload will fail if there's a real issue

        # Create a unique blob name
        blob_name = f"test-{str(uuid.uuid4())}.bin"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # Generate random data
        data = os.urandom(file_size_kb * 1024)

        # Upload the data
        blob_client.upload_blob(data, overwrite=True)

        # Download the data to verify
        blob_client.download_blob().readall()
        
        # Clean up by deleting the blob
        blob_client.delete_blob()

        response_message = {
            "message": f"Successfully uploaded and downloaded a {file_size_kb} KB file."
        }
        return func.HttpResponse(body=json.dumps(response_message), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)