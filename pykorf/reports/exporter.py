import pandas as pd
from typing import Any
from pykorf import Model
from pykorf.elements import Pipe, Pump, Compressor

class ResultExporter:
    """
    A scalable exporter to extract calculated results and input criteria from a pyKorf Model 
    and save them into a multi-sheet Excel report or DataFrame dictionary.
    
    This class correctly parses the dynamic units directly from the underlying KDF records
    and places them directly into the column headers (e.g. `[Result] Velocity [m/s]`) 
    allowing for clean, vectorized math on the columns by downstream unit converters.
    """
    def __init__(self, model: Model):
        self.model = model
        
        # ---------------------------------------------------------
        # REGISTRY: Add new element extractors here in the future
        # ---------------------------------------------------------
        self._extractors = {
            "Pipes": self._extract_pipes,
            "Pumps": self._extract_pumps,
            "Compressors": self._extract_compressors,
        }

    def generate_dataframes(self) -> dict[str, pd.DataFrame]:
        """Runs all registered extractors and returns a dictionary of DataFrames."""
        dfs = {}
        for sheet_name, extractor_func in self._extractors.items():
            data = extractor_func()
            if data:  # Only add the sheet if there are actual elements
                dfs[sheet_name] = pd.DataFrame(data)
        return dfs

    def export_to_excel(self, output_path: str) -> str:
        """Generates the DataFrames and writes them to a multi-sheet Excel file."""
        dfs = self.generate_dataframes()
        
        # Use pandas built-in excel exporter (requires openpyxl)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        return str(output_path)

    # =========================================================
    # HELPER FUNCTIONS
    # =========================================================
    
    def _fetch_kdf_data(self, element: Any, param_name: str, val_index: int, unit_index: int = -1) -> tuple[float | str, str]:
        """
        Dynamically fetches the value and the unit from a KDF record.
        In KORF, the unit is almost always the last item in the list (index -1).
        
        Returns:
            (value, unit_string)
        """
        record = element.get_param(param_name)
        val: float | str = "N/A"
        unit = ""

        if record and len(record.values) > val_index:
            raw_val = record.values[val_index]
            try:
                # Store as float to allow math in excel/pandas
                val = float(raw_val)
            except (ValueError, TypeError):
                val = str(raw_val)
                
        # Try to grab the unit if it exists
        if record and len(record.values) > abs(unit_index) or unit_index == -1:
            if len(record.values) > 0:
                raw_unit = str(record.values[unit_index]).strip()
                # Ensure it's a string, not a generic number that happens to be at the end
                if not raw_unit.replace('.','',1).replace('-','',1).isdigit():
                    unit = raw_unit

        return val, unit

    def _format_header(self, base_name: str, prefix: str, unit: str) -> str:
        """Creates a clean column header: '[Result] Velocity [m/s]'"""
        header = f"[{prefix}] {base_name}"
        if unit:
            header += f" [{unit}]"
        return header

    # =========================================================
    # ELEMENT EXTRACTORS
    # =========================================================

    def _extract_pipes(self) -> list[dict]:
        data = []
        for idx, pipe in self.model.pipes.items():
            if idx == 0: continue  
            
            dp_crit_val, dp_crit_unit = self._fetch_kdf_data(pipe, Pipe.SIZ, val_index=1, unit_index=2)
            vel_crit_val, vel_crit_unit = self._fetch_kdf_data(pipe, Pipe.SIZ, val_index=7, unit_index=8)
            
            dp_calc_val, dp_calc_unit = self._fetch_kdf_data(pipe, Pipe.DPL, val_index=0, unit_index=-1)
            vel_calc_val, vel_calc_unit = self._fetch_kdf_data(pipe, Pipe.VEL, val_index=0, unit_index=-1)

            row = {
                "Pipe Name": pipe.name,
                
                self._format_header("DP / DL Criteria", "Input", dp_crit_unit): dp_crit_val,
                self._format_header("Velocity Criteria", "Input", vel_crit_unit): vel_crit_val,
                
                self._format_header("DP / DL", "Result", dp_calc_unit): dp_calc_val,
                self._format_header("Velocity", "Result", vel_calc_unit): vel_calc_val,
            }
            data.append(row)
        return data

    def _extract_pumps(self) -> list[dict]:
        data = []
        for idx, pump in self.model.pumps.items():
            if idx == 0: continue
            
            suc_val, suc_unit = self._fetch_kdf_data(pump, Pump.PIN, val_index=1, unit_index=-1)
            dis_val, dis_unit = self._fetch_kdf_data(pump, Pump.POUT, val_index=1, unit_index=-1)
            
            flow_val, flow_unit = self._fetch_kdf_data(pump, Pump.HQACT, val_index=2, unit_index=-1)
            head_val, head_unit = self._fetch_kdf_data(pump, Pump.HQACT, val_index=0, unit_index=1)
            dp_val, dp_unit = self._fetch_kdf_data(pump, Pump.DP, val_index=1, unit_index=-1)
            
            npsha_val, npsh_unit = self._fetch_kdf_data(pump, Pump.NPSHA13, val_index=1, unit_index=-1)
            npshr_val, _ = self._fetch_kdf_data(pump, Pump.NPSHR13, val_index=1, unit_index=-1)
            
            pow_val, pow_unit = self._fetch_kdf_data(pump, Pump.POW, val_index=0, unit_index=-1)

            # New Shut-off and Vessel pressure fields
            pz_dp_val, pz_unit = self._fetch_kdf_data(pump, Pump.PZPRES, val_index=0, unit_index=-1)
            pz_suc_val, _ = self._fetch_kdf_data(pump, Pump.PZPRES, val_index=1, unit_index=-1)
            pz_dis_val, _ = self._fetch_kdf_data(pump, Pump.PZPRES, val_index=2, unit_index=-1)
            
            margin_val, _ = self._fetch_kdf_data(pump, Pump.PZRAT, val_index=1, unit_index=-1)
            
            ves_pres_val, ves_p_unit = self._fetch_kdf_data(pump, Pump.PZVES, val_index=0, unit_index=1)
            ves_lvl_val, ves_l_unit = self._fetch_kdf_data(pump, Pump.PZVES, val_index=2, unit_index=3)

            row = {
                "Pump Name": pump.name,
                
                self._format_header("Suction Pressure", "Input", suc_unit): suc_val,
                self._format_header("Discharge Pressure", "Input", dis_unit): dis_val,
                self._format_header("Shut-Off Margin", "Input", ""): margin_val,
                self._format_header("Suc Vessel Max Pressure", "Input", ves_p_unit): ves_pres_val,
                self._format_header("Suc Vessel Max Level", "Input", ves_l_unit): ves_lvl_val,
                
                self._format_header("Volumetric Flow", "Result", flow_unit): flow_val,
                self._format_header("Head", "Result", head_unit): head_val,
                self._format_header("Differential Pressure", "Result", dp_unit): dp_val,
                self._format_header("Hydraulic Power", "Result", pow_unit): pow_val,
                
                self._format_header("NPSH Available", "Result", npsh_unit): npsha_val,
                self._format_header("NPSH Required", "Result", npsh_unit): npshr_val,
                
                self._format_header("Shut-Off DP", "Result", pz_unit): pz_dp_val,
                self._format_header("Suction Max Pressure", "Result", pz_unit): pz_suc_val,
                self._format_header("Discharge Shut-Off Pressure", "Result", pz_unit): pz_dis_val,
            }
            data.append(row)
        return data

    def _extract_compressors(self) -> list[dict]:
        data = []
        for idx, comp in self.model.compressors.items():
            if idx == 0: continue
            
            flow_val, flow_unit = self._fetch_kdf_data(comp, Compressor.QACT, val_index=0, unit_index=-1)
            dp_val, dp_unit = self._fetch_kdf_data(comp, Compressor.DP, val_index=1, unit_index=-1)
            
            row = {
                "Compressor Name": comp.name,
                
                self._format_header("Gas Volumetric Flow", "Result", flow_unit): flow_val,
                self._format_header("Differential Pressure", "Result", dp_unit): dp_val,
            }
            data.append(row)
        return data
