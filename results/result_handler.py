#!/usr/bin/env python3
import os
import argparse

def process_all_files(root_dir):
    """
    Recursively process all files in the given root_dir and its subdirectories,
    aggregating benchmark data. Each file is expected to have lines with three columns:
    an integer key and two float metrics.
    
    Returns:
        data (dict): Dictionary mapping each key to a list: [sum_metric1, sum_metric2, count].
    """
    data = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # Skip any existing output files to avoid reprocessing them
            if filename == "output.out":
                continue
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r') as file:
                        for line in file:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split()
                            # Skip lines that do not have at least three columns
                            if len(parts) < 3:
                                continue
                            try:
                                key = int(parts[0])
                                metric1 = float(parts[1])
                                metric2 = float(parts[2])
                            except ValueError:
                                continue  # Skip lines that cannot be parsed
                            
                            if key not in data:
                                data[key] = [0.0, 0.0, 0]
                            data[key][0] += metric1
                            data[key][1] += metric2
                            data[key][2] += 1
                except Exception as e:
                    print(f"Error reading file {filepath}: {e}")
    return data

def write_output_file(root_dir, data):
    """
    Write the aggregated benchmark data to an output file (output.out) at the root_dir.
    The file will have the same structure as the original benchmark files.
    """
    output_path = os.path.join(root_dir, "output.out")
    try:
        with open(output_path, 'w') as outfile:
            # Write keys in sorted order to preserve consistency.
            for key in sorted(data.keys()):
                sum1, sum2, count = data[key]
                avg1 = sum1 / count
                avg2 = sum2 / count
                outfile.write("{:8d} {:12.6f} {:14.8f}\n".format(key, avg1, avg2))
        print(f"Output written to: {output_path}")
    except Exception as e:
        print(f"Error writing to output file {output_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Recursively process all benchmark files in a folder and aggregate their results into a single output.out at the root."
    )
    parser.add_argument("input_directory", help="The directory to process recursively")
    args = parser.parse_args()

    aggregated_data = process_all_files(args.input_directory)
    if aggregated_data:
        write_output_file(args.input_directory, aggregated_data)
    else:
        print("No valid benchmark data found.")

if __name__ == "__main__":
    main()
