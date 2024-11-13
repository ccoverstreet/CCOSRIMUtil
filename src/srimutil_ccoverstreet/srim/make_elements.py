with open("ATOMDATA") as f:
    lines = []
    for i, line in enumerate(f):
        if i < 2 or line.startswith("(c)"):
            continue

        split = line.replace("\"", "").split()
        lines.append(split)

script_header = """
# Auto-generated python file from make_elements.py
from dataclasses import dataclass

@dataclass()
class ElementData():
    atomic_number: int
    symbol: str
    name: str
    MAI_mass: int
    MAI_weight: float
    natural_weight: float
    density: float
    atomic_density: float
    fermi_velocity: float
    heat_subl: float
    gasdens: float
    gas_density: float

"""

with open("elements.py", "w") as f:
    f.write(script_header)
    f.write("ELEM_DICT = {\n")
    for line in lines:
        f.write(f"\"{line[1]}\": ElementData({line[0]}, \"{line[1]}\", \"{line[2]}\", {line[3]}, {line[4]}, {line[5]}, {line[6]}, {line[7]}, {line[8]}, {line[9]}, {line[10]}, {line[11]}),\n")

    
    f.write("}")
        

