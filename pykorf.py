import os
import time

from pywinauto.application import Application

# --- CONFIGURATION ---
# The path to your Korf model file
MODEL_FILE = r"Pumpcases.kdf"
# The path to your Korf executable (used for connecting to the process)
KORF_PATH = r"C:\Program Files (x86)\Korf 36\Korf_36.exe"


def update_flow_rate(file_path, new_flows_string):
    """Updates the TFLOW (Flow Rate) for Pipe 1 (L1) in the text file.
    new_flows_string: e.g., "60;65;25" for three cases.
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False

    with open(file_path) as f:
        lines = f.readlines()

    with open(file_path, "w") as f:
        for line in lines:
            # We target Pipe 1 (L1) and the TFLOW parameter
            if r'"\PIPE",1,"TFLOW"' in line:
                # Korf format: "\PIPE",1,"TFLOW","50;55;20",20,"t/h"
                parts = line.split(",")
                parts[3] = f'"{new_flows_string}"'
                line = ",".join(parts)
            f.write(line)

    print(f"File updated with flow rates: {new_flows_string}")
    return True


def get_calculated_results(file_path):
    """Parses the saved file to extract calculated results for Pump 1."""
    results = {"Power_kW": None, "Head_m": None, "Efficiency": None}
    with open(file_path) as f:
        for line in f:
            if r'"\PUMP",1,"POW"' in line:
                results["Power_kW"] = line.split(",")[3]
            if r'"\PUMP",1,"HQACT"' in line:
                results["Head_m"] = line.split(",")[3]
            if r'"\PUMP",1,"EFFP"' in line:
                # Format: "\PUMP",1,"EFFP",";C",.351
                results["Efficiency"] = line.split(",")[-1].strip()
    return results


def run_korf_cycle(flow_input):
    """Connects to Korf, runs the model, and extracts results."""
    try:
        # 1. Update the underlying file
        update_flow_rate(MODEL_FILE, flow_input)

        # 2. Connect to the EXISTING Korf instance (Preserves trial opens)
        print("Connecting to Korf...")
        app = Application(backend="win32").connect(path=KORF_PATH)
        main_dlg = app.top_window()
        main_dlg.set_focus()

        # 3. Reload the file in Korf to pick up the text changes
        # We simulate Ctrl+O, type filename, and Enter
        print("Reloading model...")
        main_dlg.type_keys("^o")
        time.sleep(1)
        open_dlg = app.window(title_re=".*Open.*")
        open_dlg.Edit.set_edit_text(os.path.abspath(MODEL_FILE))
        open_dlg.type_keys("{ENTER}")
        time.sleep(2)

        # Re-acquire the top window after the file is (re)opened,
        # so subsequent actions target the newly loaded document
        # instead of the previous stale window.
        main_dlg = app.top_window()
        main_dlg.set_focus()

        # 4. Trigger the RUN command via the menu hierarchy
        print("Triggering Hydraulics Run...")
        main_dlg.menu_select("Hydraulics -> Hydraulics -> Run")

        # 5. Handle the Runlog popup
        print("Waiting for calculation to finish...")
        try:
            # We wait up to 20 seconds for the solver
            runlog = app.window(title="Runlog")
            runlog.wait("visible", timeout=20)
            runlog.OK.click()
            print("Runlog acknowledged.")
        except:
            print("Runlog did not appear (may have finished too fast).")

        # 6. Save results back to the text file
        print("Saving results...")
        main_dlg.type_keys("^s")
        time.sleep(1)

        # 7. Extract and print results
        data = get_calculated_results(MODEL_FILE)
        print("\n--- CALCULATED PUMP RESULTS ---")
        print(f"Operating Head:  {data['Head_m']} m")
        print(f"Absorbed Power:  {data['Power_kW']} kW")
        print(f"Efficiency:      {data['Efficiency']}")
        print("-------------------------------\n")

    except Exception as e:
        print(f"Automation failed: {e}")


if __name__ == "__main__":
    # Example usage: Change flow for Normal;Rated;Min cases
    # Run this without closing Korf!
    target_flows = "55;60;25"
    run_korf_cycle(target_flows)
