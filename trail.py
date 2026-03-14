"""Trail script for testing the use_case module with simplified API.

This script demonstrates both the simplified function-based API and the
legacy PipedataProcessor class-based API.
"""

import logging

from pykorf import Model
from pykorf.reports.exporter import ResultExporter

# Configure logging to show INFO level and above
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

KORF_FILE = r"pykorf/trail_files/Cooling Water Circuit.kdf"

model = Model(KORF_FILE)
# Demonstration of summary() methods
print("\n[5/5] Demonstration of summary() methods and unit conversion...")


# Pipes
if model.pipes:
    # Use the first real instance (index 0 is the template)
    pipe = next(p for idx, p in model.pipes.items() if idx > 0)
    print(f"\n      --- Pipe: {pipe.name} ---")
    print("      Standard Summary (Dictionary):")
    print(f"      {pipe.summary()}")

    print("\n      Export Summary (Rich Headers & Units - Before Conversion):")
    for key, val in pipe.summary(export=True).items():
        print(f"        {key:35}: {val}")

# Exporter with Unit Conversion
print("\n      --- Result Exporter (After Unit Conversion) ---")
exporter = ResultExporter(model)
dfs = exporter.generate_dataframes()

if "Pipes" in dfs:
    pipe_df = dfs["Pipes"]
    # Show the first row's dictionary representation to match the format
    first_pipe = pipe_df.iloc[0].to_dict()
    print("\n      Converted Export Summary:")
    for key, val in first_pipe.items():
        print(f"        {key:35}: {val}")

print("\nDone!")
