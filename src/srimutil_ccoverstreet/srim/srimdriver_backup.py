import subprocess
import os
from dataclasses import dataclass
from enum import Enum
import sys
import numpy as np

PROGRAM_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

@dataclass()
class ElementData():
    atomic_number: int
    symbol: str
    name: str
    MAI_mass: int
    MAI_weight: float
    natural_weight: float


# Preload Elemental Data
def load_element_data(filename):
    data = []
    elem_dict = {}
    with open(filename) as f:
        for i, line in enumerate(f):
            if i < 2 or line.startswith("(c)"): 
                continue

            split = line.replace("\"", "").split()

            elem_dict[split[1]] = ElementData(
                int(split[0]),
                split[1],
                split[2],
                int(split[3]),
                float(split[4]),
                float(split[5])
            )

    return elem_dict


ELEM_DICT = load_element_data(f"{PROGRAM_DIR}/data/ATOMDATA")


class TargetType(Enum):
    SOLID = 0
    GAS = 1

@dataclass()
class SRIMConfig:
    output_name: str
    ion: ElementData
    target_type: TargetType
    density: float
    compound_corr: float
    stoich: [float]
    elements: [ElementData]
    min_energy: float
    max_energy: float

    def to_input_file_str(self):
        buffer = "---Stopping/Range Input Data (Number-format: Period = Decimal Point)\n"
        buffer += "---Output File Name\n"
        buffer += f"\"{self.output_name}\"" + "\n"
        buffer += "---Ion(Z), Ion Mass(u)\n"
        buffer += f"{self.ion.atomic_number}   {self.ion.MAI_weight}\n"
        buffer += "---Target Data: (Solid=0,Gas=1), Density(g/cm3), Compound Corr.\n"
        buffer += f"{self.target_type.value} {self.density} {self.compound_corr}\n"
        buffer += "---Number of Target Elements\n"
        buffer += f"{len(self.stoich)}\n"
        buffer += "---Target Elements: (Z), Target name, Stoich, Target Mass(u)\n"
        for i in range(0, len(self.stoich)):
            elem = self.elements[i]
            buffer += f"{elem.atomic_number} \"{elem.name}\" {self.stoich[i]} {elem.natural_weight}\n"

        buffer += "---Output Stopping Units (1-8)\n"
        buffer += "5\n"
        buffer += "---Ion Energy : E-Min(keV), E-Max(keV)\n"
        buffer += f"{self.min_energy} {self.max_energy}\n"

        return buffer


def run_srim_config(srim_config):
    sr_in = f"{PROGRAM_DIR}/srim/SR.IN"
    with open(sr_in, "w", newline="\r\n") as f:
    #with open(sr_in, "w", newline="\n") as f:
        f.write(srim_config.to_input_file_str())

    subprocess.run(PROGRAM_DIR + "/srim/" + "SRModule.exe", cwd=PROGRAM_DIR + "/srim")


# -------------------- POST PROCESSING --------------------

# These mults are use to convert all length units to micrometers
MULTS = {
    "A": 1E-4,
    "um": 1,
    "mm": 1E3,
    "keV": 1,
    "MeV": 1E3,
    "GeV": 1e6
}

@dataclass
class SrimData:
    rho: float
    data: np.array

# Convert all to keV and micron
def read_srim_output_file(filename):
    with open(filename) as f:
        collect = False
        collect_count = 0
        out = []
        conversion = 1.0
        rho = 1.0

        for line in f:
            stripped = line.strip()


            if stripped.startswith("-----"):
                collect = not collect
                collect_count += 1
                continue

            if not collect: 
                if "Density" in stripped:
                    rho = float(stripped.replace("Target", "").split()[2])

            if collect and collect_count < 2:
                split_line = line.split()
                #print(split_line)
                row = []
                row.append(float(split_line[0]) * MULTS[split_line[1]])
                row.append(float(split_line[2]))
                row.append(float(split_line[3]))
                row.append(float(split_line[4]) * MULTS[split_line[5]])
                row.append(float(split_line[6]) * MULTS[split_line[7]])
                row.append(float(split_line[8]) * MULTS[split_line[9]])

                out.append(row)
            elif collect and collect_count >= 2:
                # We only care about this line
                if "keV" in line and "micron" in line:
                    conversion = float(line.split()[0])

        # Use conversion to change energy loss to keV / micron
        print(f"Conversion = {conversion}")
        out = np.array(out)
        out[:, 1] = out[:, 1] * conversion
        out[:, 2] = out[:, 2] * conversion



        return SrimData(rho, out)

def range_to_depth(range_data):
    return range_data[-1] - range_data

# Convert keV / micron to keV / nm
# Make sure to pass in rho adjusted by packing fraction
def dedx_to_kev_nm(eloss):
    return eloss / 1000

def find_index_before_stopping(dx_depth, dx_total_dedx):
    # Cut off steep drop that appears on right hand side
    # Iterate through to remove section with steep slope
    evaluate = lambda pos: dx_total_dedx[pos]


    pos = 0
    while pos < len(dx_total_dedx) and (evaluate(pos) < 0):
        #print(pos, dx_depth[pos], dx_total_dedx[pos], evaluate(pos))
        pos += 1

    return pos

@dataclass
class ProcessConfig:
    srim_file: str
    output_file: str
    rho: float
    packing: float

@dataclass 
class ConversionConfig:
    rho: float
    packing: float

def convert_srim_to_table(srim_data, conv_config: ConversionConfig):
    rho = conv_config.rho
    packing_frac = conv_config.packing

    data = srim_data.data

    # Apply correction in case new density is different from density
    # in SRIM file
    rho_corr = rho / srim_data.rho

    # Get basic columns
    energies = data[:, 0]
    depth = range_to_depth(data[:, 3]) / packing_frac / rho_corr
    elec_dedx = dedx_to_kev_nm(data[:,1]) * rho_corr
    nuclear_dedx = dedx_to_kev_nm(data[:, 2]) * rho_corr
    total_dedx = elec_dedx + nuclear_dedx


    return np.vstack((depth, elec_dedx, nuclear_dedx, elec_dedx + nuclear_dedx, energies)).T


if __name__ == "__main__":
    #subprocess.run()
    conf = SRIMConfig(
        "testfile",
        ELEM_DICT["Au"],
        TargetType.SOLID,
        6.15,
        1,
        [1, 1],
        [ELEM_DICT["Ga"], ELEM_DICT["N"]],
        10,
        946000
    )

    run_srim_config(conf)



