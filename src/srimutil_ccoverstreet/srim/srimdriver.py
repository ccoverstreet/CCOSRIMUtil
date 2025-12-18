import subprocess
import os
from dataclasses import dataclass
from enum import Enum
import sys
import numpy as np
import importlib.resources
from .elements import *

MODULE_PATH = importlib.resources.files(__package__)
print(MODULE_PATH)


class TargetType(int, Enum):
    SOLID = 0
    GAS = 1

    

@dataclass()
class SRIMLayer:
    target_type: TargetType
    density: float
    compound_corr: float
    stoich: [float]
    elements: [ElementData]
    thickness: float # thickness in micrometers
    name: str

    def to_json(self):
        return {
            "target_type": self.target_type,
            "density": self.density,
            "compound_corr": self.compound_corr,
            "stoich": self.stoich,
            "elements": list(map(lambda e: e.to_json(), self.elements)),
            "thickness": self.thickness,
            "name": self.name
        }


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
        buffer += f"{round(self.min_energy, 1)} {round(self.max_energy, 1)}\n"
        # Doing this just completely fucks SR module...
        # Removes range estimation which is the whole point
        #buffer += "0 0\n"

        #n = 500
        #start = np.log10(self.min_energy)
        #end = np.log10(self.max_energy)
        #energies = 10 ** np.linspace(start, end, n)
        #for e in energies:
        #    buffer += f"{e}\n"

        #buffer += "0\n"

        return buffer


def run_srim_config(srim_config):
    sr_in = f"{str(MODULE_PATH)}/SR.IN"
    with open(sr_in, "w", newline="\r\n") as f:
        f.write(srim_config.to_input_file_str())

    if sys.platform == "win32":
        ret = subprocess.run('"' + str(MODULE_PATH) + "/" + "SRModule.exe" + '"', cwd=str(MODULE_PATH), capture_output=True)
    elif sys.platform == "linux":
        ret = subprocess.run(["wine", str(MODULE_PATH) + "/" + "SRModule.exe"], cwd=str(MODULE_PATH), capture_output=True)
    else:
        raise Exception("Mac not supported")

    if ret.returncode != 0:
        raise Exception("Unable to run SR Module" + str(ret))



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


# Utility Library and Script for SRIM output analysis
# Cale Overstreet
# Testers: George Adamson 
# Comes with a CLI tool (use `python3 thisscript.py --help` to see options)

# These mults are use to convert all length units to micrometers
MULTS = {
    "A": 1E-4,
    "um": 1,
    "mm": 1E3,
    "m": 1E6,
    "km": 1E9,
    "keV": 1,
    "MeV": 1E3,
    "GeV": 1e6
}

@dataclass
class SRIMData:
    rho: float
    energy: np.array
    dedx_elec: np.array
    dedx_nuc: np.array
    proj_range: np.array
    long_straggling: np.array
    lat_straggling: np.array

# Convert all to keV and micron
def read_srim_output(filename):
    with open(filename) as f:
        collect = False
        collect_count = 0
        out = []
        out.append([0, 0, 0, 0, 0, 0])
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

        energy = out[:, 0].T
        elec = out[:, 1].T
        nuc = out[:, 2].T
        proj_range = out[:, 3].T
        long_straggling = out[:, 4].T
        lat_straggling = out[:, 5].T

        return SRIMData(rho, energy, elec, nuc,
                        proj_range, long_straggling, lat_straggling)

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

@dataclass
class SRIMTable:
    # Data is reordered so that depth is increasing 
    rho: float
    packing_frac: float
    depth: np.array
    dedx_elec: np.array
    dedx_nuc: np.array
    dedx_total: np.array
    energy: np.array
    long_straggling: np.array
    lat_straggling: np.array

    def to_numpy(self):
        return np.vstack([
            self.depth,
            self.dedx_elec,
            self.dedx_nuc,
            self.dedx_total,
            self.energy,
            self.long_straggling,
            self.lat_straggling
        ]).T

    def save_to_file(self, filepath):
        with open(filepath, "w") as f:
            f.write(f"# rho = {self.rho}\n")
            f.write(f"# packing fraction = {self.packing_frac}\n")
            f.write(f"# Depth [micron], de/dx elec., de/dx nuc., de/dx total, Energy [keV], long. straggling [micron], lat. straggling [micron]\n")
            for i in range(0, len(self.depth)):
                f.write(f"{self.depth[i]}, {self.dedx_elec[i]}, {self.dedx_nuc[i]}, {self.dedx_total[i]}, {self.energy[i]}, {self.long_straggling[i]}, {self.lat_straggling[i]}\n")
                


def convert_srim_to_table(srim_data: SRIMData, conv_config: ConversionConfig):
    """Converts SRIMData to SRIMTable with depths corrected for density and packing fraction

    Parameters
    ----------
    srim_data : SRIMData
    conv_config: ConversionConfig
        Contains density and packing fraction used in post-processing

    Returns
    -------
    srim_table: SRIMTable
    """
    rho = conv_config.rho
    packing_frac = conv_config.packing

    # Apply correction in case new density is different from density
    # in SRIM file
    rho_corr = rho / srim_data.rho

    # Get basic columns
    # MAKE SURE DATA IS FLIPPED
    # We assume isotropic material proerties when converting
    # range and straggling. Conversion for range and straggling
    # is assumed to be identical.
    data = srim_data
    energy = np.flip(data.energy)
    depth = np.flip(range_to_depth(data.proj_range) / packing_frac / rho_corr)
    elec_dedx = np.flip(dedx_to_kev_nm(data.dedx_elec) * rho_corr)
    nuclear_dedx = np.flip(dedx_to_kev_nm(data.dedx_nuc) * rho_corr)
    total_dedx = np.flip(elec_dedx + nuclear_dedx)
    long_straggling = np.flip(range_to_depth(data.long_straggling) / packing_frac / rho_corr)
    lat_straggling = np.flip(range_to_depth(data.lat_straggling) / packing_frac / rho_corr)


    return SRIMTable(
        conv_config.rho, conv_config.packing,
        depth, elec_dedx, nuclear_dedx,
        elec_dedx + nuclear_dedx, energy,
        long_straggling, lat_straggling
    )


@dataclass
class IonConfigLayer:
    ion: ElementData
    energy: float

    def to_json(self):
        return {
            "element": self.ion.to_json(),
            "energy": self.energy
        }

@dataclass 
class SRIMLayerResult:
    combined: np.array # Table array
    boundaries: np.array # boundaries between

    def to_json(self):
        return {
            "combined": list(self.combined),
            "boundaries": list(self.boundaries)
        }


@dataclass
class SRIMLayerProject:
    ion: IonConfigLayer
    layers: [SRIMLayer]
    result: SRIMLayerResult

    def to_json(self):
        return {
            "ion": self.ion.to_json(),
            "layers": list(map(lambda l: l.to_json(), self.layers)),
            "result": self.result.to_json()
        }

def run_srim_layered(ion_config: IonConfigLayer, layers: [SRIMLayer], output_dir: str):
    E_0 = ion_config.energy  
    prev_x = 0

    chunks = []
    boundaries = []

    for i_layer, layer in enumerate(layers):
        output_name = f"{output_dir}/{i_layer:03d}_{layer.name}.srim"

        conf = SRIMConfig(
            output_name,
            ion_config.ion,
            layer.target_type,
            layer.density,
            layer.compound_corr,
            layer.stoich,
            layer.elements,
            10, # energy in keV
            E_0
        )

        run_srim_config(conf)
        table = convert_srim_to_table(read_srim_output(output_name),
                                      ConversionConfig(layer.density, 1.0))
        # find index of depth
        ind = np.argmax(table.depth > layer.thickness)

        # Interpolate to find values at layer boundary
        # Assuming energy loss as a function of depth is linear
        # within interpolation region
        depth = layer.thickness
        nuclear = np.interp(depth, table.depth, table.dedx_nuc)
        electronic = np.interp(depth, table.depth, table.dedx_elec)
        total = np.interp(depth, table.depth, table.dedx_total)
        boundary_energy = np.interp(depth, table.depth, table.energy)

        # Add previous boundary point to all x values
        table.depth = table.depth + prev_x

        E_0 = boundary_energy
        if ind == 0:
            # layer thickness is larger than ion range
            chunk = table.to_numpy()[:, :-2]
        else:
            # Ion range is larger than layer
            chunk = np.vstack((
                table.to_numpy()[:ind, :-2],
                np.array([depth + prev_x, electronic, nuclear, total, boundary_energy])
            ))

        chunks.append(chunk)

        # Increment values for next loop
        prev_x += depth

        boundaries.append(prev_x)



    combined = np.vstack(chunks)
    np.savetxt(output_dir + "/" + "combined.dat", combined)

    proj = SRIMLayerProject(ion_config, layers,
                     SRIMLayerResult(combined.tolist(), np.array(boundaries).tolist()))

    return proj
