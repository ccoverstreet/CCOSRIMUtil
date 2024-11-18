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


class TargetType(Enum):
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


