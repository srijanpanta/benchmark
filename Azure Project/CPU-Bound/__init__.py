import logging
import azure.functions as func
import numpy as np
import time
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('CPU-Bound benchmark function processed a request.')

    try:
        req_body = req.get_json()
        size = int(req_body.get('size', 200)) # Default to 200x200 if not provided
    except (ValueError, AttributeError):
        size = 200 # Default size if JSON is invalid or missing

    # Create two random square matrices of the given size
    matrix_a = np.random.rand(size, size)
    matrix_b = np.random.rand(size, size)

    # Perform the multiplication and time it
    start_time = time.time()
    result_matrix = np.matmul(matrix_a, matrix_b)
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000

    response_message = {
        "message": f"Successfully multiplied two {size}x{size} matrices.",
        "duration_ms": round(duration_ms, 2)
    }

    return func.HttpResponse(
        body=json.dumps(response_message),
        mimetype="application/json",
        status_code=200
    )