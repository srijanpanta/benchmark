import requests
import json
import time
import csv
import statistics
import numpy as np

# --- CONFIGURATION ---
# Define the test cases you want to run
# The script will iterate through all of these automatically.
TEST_CASES = [
    {"platform": "AWS",   "test_type": "CPU-Bound", "payload": {"size": 300}},
    {"platform": "AWS",   "test_type": "CPU-Bound", "payload": {"size": 1000}},
    {"platform": "AWS",   "test_type": "IO-Bound",  "payload": {"file_size_kb": 256}},
    {"platform": "AWS",   "test_type": "IO-Bound",  "payload": {"file_size_kb": 1024}},

    {"platform": "Azure", "test_type": "CPU-Bound", "payload": {"size": 300}},
    {"platform": "Azure", "test_type": "CPU-Bound", "payload": {"size": 1000}},
    {"platform": "Azure", "test_type": "IO-Bound",  "payload": {"file_size_kb": 256}},
    {"platform": "Azure", "test_type": "IO-Bound",  "payload": {"file_size_kb": 1024}},
]

# Define the number of requests for each performance test run
NUM_REQUESTS = 1000 # Use 100 for quick tests, 1000+ for final data.

# --- SCRIPT ---

def run_warmup(url, payload, num_requests=10):
    """Warms up the function by sending a few initial requests."""
    print(f"--- Running {num_requests} warmup requests for {url}... ---")
    for i in range(num_requests):
        try:
            requests.post(url, json=payload, timeout=60)
        except requests.exceptions.RequestException as e:
            print(f"Warmup request failed: {e}")
    print("--- Warmup complete. ---\n")

def run_performance_test(url, payload, num_requests):
    """Runs a load test to measure warm execution performance."""
    print(f"--- Running Performance Test: {num_requests} requests ---")
    results = []
    total_start_time = time.time()

    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=60)
            end_time = time.time()
            
            result_entry = {
                "request_id": i + 1,
                "status_code": response.status_code,
                "end_to_end_latency_ms": None,
                "server_duration_ms": None,
                "network_latency_ms": None
            }

            if response.status_code == 200:
                end_to_end_latency = (end_time - start_time) * 1000
                server_duration = response.json().get('duration_ms')

                result_entry["end_to_end_latency_ms"] = round(end_to_end_latency, 2)
                if server_duration is not None:
                    result_entry["server_duration_ms"] = server_duration
                    result_entry["network_latency_ms"] = round(end_to_end_latency - server_duration, 2)

                print(f"Request {i+1}/{num_requests} | Success | Latency: {end_to_end_latency:.2f} ms")
            else:
                print(f"Request {i+1}/{num_requests} | Failed  | Status Code: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"Request {i+1}/{num_requests} | Failed  | Timeout")
            result_entry["status_code"] = "Timeout"
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1}/{num_requests} | Failed  | Error: {e}")
            result_entry["status_code"] = "ConnectionError"
        
        results.append(result_entry)
        time.sleep(0.1)

    total_duration = time.time() - total_start_time
    return results, total_duration

def analyze_and_save_results(results, total_duration, platform, test_type, payload, filename):
    """Saves data to CSV and prints a detailed analysis."""
    if not results:
        print("No results to analyze.")
        return

    # --- Save full raw data to CSV ---
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['request_id', 'status_code', 'end_to_end_latency_ms', 'server_duration_ms', 'network_latency_ms']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nFull results for {len(results)} requests saved to {filename}")

    # --- Data Extraction for Analysis ---
    successful_results = [r for r in results if r['status_code'] == 200 and r.get('end_to_end_latency_ms') is not None]
    failed_results = [r for r in results if r['status_code'] != 200]
    
    if not successful_results:
        print("No successful requests to analyze.")
        return

    e2e_latencies = [r['end_to_end_latency_ms'] for r in successful_results]
    
    # --- Print Detailed Summary ---
    print("\n" + "="*50)
    print(f"  Detailed Benchmark Analysis: {platform} - {test_type} - Payload: {payload}")
    print("="*50)

    # 1. Reliability Metrics
    print("\n[1] Reliability & Success Metrics")
    success_count = len(successful_results)
    total_count = len(results)
    print(f"Success Rate:         {success_count}/{total_count} ({success_count/total_count:.2%})")
    print(f"Failure Count:        {len(failed_results)}")
    
    # 2. End-to-End Latency Analysis
    print("\n[2] End-to-End Latency Analysis (Client Perspective)")
    print(f"Average (Mean):       {statistics.mean(e2e_latencies):.2f} ms")
    print(f"p50 (Median):         {statistics.median(e2e_latencies):.2f} ms")
    print(f"p95:                  {np.percentile(e2e_latencies, 95):.2f} ms")
    print(f"Best (Min):           {min(e2e_latencies):.2f} ms")
    print(f"Worst (Max):          {max(e2e_latencies):.2f} ms")
    
    # 3. Performance Consistency & Jitter Analysis
    if len(e2e_latencies) > 1:
        print("\n[3] Performance Consistency (Jitter)")
        std_dev = statistics.stdev(e2e_latencies)
        mean_val = statistics.mean(e2e_latencies)
        cv = (std_dev / mean_val) * 100 if mean_val > 0 else 0
        print(f"Standard Deviation:   {std_dev:.2f} ms")
        print(f"Coefficient of Var.:  {cv:.2f}% (Lower is more consistent)")

    # 4. Throughput Analysis
    if total_duration > 0:
        print("\n[4] Throughput Analysis")
        throughput = success_count / total_duration
        print(f"Total Test Time:      {total_duration:.2f} seconds")
        print(f"Avg. Throughput:      {throughput:.2f} requests/sec")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    
    # --- This is the main execution block ---
    
    # Your specific deployment endpoints
    URLS = {
        "AWS": {
            "CPU-Bound": "https://fagy8bkn21.execute-api.eu-west-2.amazonaws.com/Prod/cpu-bound",
            "IO-Bound": "https://fagy8bkn21.execute-api.eu-west-2.amazonaws.com/Prod/io-bound"
        },
        "Azure": {
            "CPU-Bound": "https://azure-benchmarks-77227232.azurewebsites.net/api/CPU-Bound",
            "IO-Bound": "https://azure-benchmarks-77227232.azurewebsites.net/api/IO-Bound"
        }
    }
    
    # Main loop to run all test cases automatically
    for i, case in enumerate(TEST_CASES):
        platform = case["platform"]
        test_type = case["test_type"]
        payload = case["payload"]
        
        print("\n" + "#"*70)
        print(f"### Starting Test Case {i+1}/{len(TEST_CASES)}: {platform} - {test_type} - Payload: {payload} ###")
        print("#"*70)
        
        target_url = URLS.get(platform, {}).get(test_type)
        if not target_url:
            print(f"ERROR: URL not found for {platform} - {test_type}. Skipping test.")
            continue
            
        # Dynamically generate the CSV filename for this test run
        payload_value = payload.get('size') or payload.get('file_size_kb')
        csv_filename = f"results_{platform.lower()}_{test_type.lower().replace('-','')}_{payload_value}.csv"

        # 1. Warm up the function
        run_warmup(target_url, payload)
        
        # 2. Run the main performance test
        performance_results, total_test_duration = run_performance_test(target_url, payload, num_requests=NUM_REQUESTS)
        
        # 3. Analyze the results and save to CSV
        analyze_and_save_results(performance_results, total_test_duration, platform, test_type, payload, csv_filename)

        print(f"### Test Case {i+1}/{len(TEST_CASES)} Complete. ###")
        
        # Add a delay between major test runs to let platforms cool down
        if i < len(TEST_CASES) - 1:
            print("\n--- Pausing for 60 seconds before next test case... ---")
            time.sleep(60)

    print("\n\nAll benchmark tests completed! 🎉")