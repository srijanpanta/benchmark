import gzip
import shutil
import glob
import os

input_folder = "Cloudwatch Exports"
output_folder = "decompressed"

os.makedirs(output_folder, exist_ok=True)

# Fix the path concatenation
for gz_file in glob.glob(os.path.join(input_folder, "*.gz")):
    output_file = os.path.join(output_folder, os.path.basename(gz_file).replace(".gz", ""))
    with gzip.open(gz_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Decompressed: {gz_file} -> {output_file}")

print("All files decompressed successfully!")
