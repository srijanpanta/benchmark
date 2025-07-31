import json
import numpy as np
import time
import boto3
import os
import uuid

# --- Benchmark Function 1: CPU-Intensive (Matrix Multiplication) ---
def cpu_bound_handler(event, context):
    """
    Handles CPU-bound benchmark requests.
    """
    try:
        # AWS API Gateway passes the request body as a string, so we need to parse it
        body = json.loads(event.get("body", "{}"))
        size = int(body.get('size', 200))
    except (ValueError, AttributeError):
        size = 200

    matrix_a = np.random.rand(size, size)
    matrix_b = np.random.rand(size, size)

    start_time = time.time()
    result_matrix = np.matmul(matrix_a, matrix_b)
    end_time = time.time()

    duration_ms = (end_time - start_time) * 1000

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Successfully multiplied two {size}x{size} matrices.",
            "duration_ms": round(duration_ms, 2)
        }),
    }

# --- Benchmark Function 2: I/O-Bound (S3 File Operation) ---
def io_bound_handler(event, context):
    """
    Handles I/O-bound benchmark requests.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        file_size_kb = int(body.get('file_size_kb', 1024))
    except (ValueError, AttributeError):
        file_size_kb = 1024

    # This gets the bucket name from an environment variable set in template.yaml
    bucket_name = os.environ.get("S3_BUCKET_NAME")
    if not bucket_name:
        return {"statusCode": 500, "body": json.dumps({"error": "S3_BUCKET_NAME environment variable not set."})}

    s3 = boto3.client('s3')
    blob_name = f"test-{str(uuid.uuid4())}.bin"
    data = os.urandom(file_size_kb * 1024)

    try:
        # Upload
        s3.put_object(Bucket=bucket_name, Key=blob_name, Body=data)
        # Download
        s3.get_object(Bucket=bucket_name, Key=blob_name)
        # Clean up by deleting the test file
        s3.delete_object(Bucket=bucket_name, Key=blob_name)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Successfully uploaded and downloaded a {file_size_kb} KB file from S3."
            }),
        }
    except Exception as e:
        print(f"Error during S3 operation: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}