from srimutil_ccoverstreet import srim, postprocess
import numpy as np
import matplotlib.pyplot as plt
import os

def main():
    output_filename = "mylayer.dat"
    E0 = 946000 # keV
    E_min = 10 # keV
    ion = srim.ELEM_DICT["Au"]
    layers_new = [
        srim.SRIMLayer(srim.TargetType.SOLID,
            6.15,
            1, # compound correction
            [1, 1],
            [srim.ELEM_DICT["Ga"], srim.ELEM_DICT["N"]],
            1), # layer thickness in micrometers
        srim.SRIMLayer(srim.TargetType.SOLID,
            3.26,
            1,
            [1, 1],
            [srim.ELEM_DICT["Al"], srim.ELEM_DICT["N"]],
            1),
        srim.SRIMLayer(srim.TargetType.SOLID,
            3.21,
            1,
            [1, 1],
            [srim.ELEM_DICT["Si"], srim.ELEM_DICT["C"]],
            60)
    ]

    E_cur = E0
    prev_x = 0 # Cur x position of the ion the "stack"
    boundaries = [] # Use for marking the depths for each layer boundary 
    chunks = [] # Chunks of the output table we are generating
    for layer in layers_new:
        print("\n\n")
        print(f"Ion energy: {E_cur}")
        boundaries.append(prev_x + layer.thickness)

        srim_output_file = f"{os.getcwd()}/testfile"
        #srim_output_file = f"testfile"

        srim_conf = srim.SRIMConfig(
            srim_output_file,
            ion,
            layer.target_type,
            layer.density,
            layer.compound_corr,
            layer.stoich,
            layer.elements,
            E_min,
            E_cur
        )

        # Run the generated srim config
        srim.run_srim_config(srim_conf)

        # Load the table and reverse so depths are in increasing order
        table = postprocess.convert_srim_to_table(postprocess.read_file(srim_output_file),
                                   srim.ConversionConfig(layer.density, 1.0))

        # Find where depth in table is greater than layer
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

        E_cur = boundary_energy
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

        print(chunk)


        # Increment values for next loop
        prev_x += depth

        # Plot current table as sanity check
        plt.plot(table.depth, table.dedx_total, marker="o")
        plt.plot(table.depth, table.dedx_nuc, marker="o")
        plt.plot(table.depth, table.dedx_elec, marker="o")
        plt.show()


    # Created combined SRIM table for layers
    combined = np.vstack(chunks)
    np.savetxt(output_filename, combined)

    # Plot for sanity check
    plt.plot(combined[:, 0], combined[:, 3], label="Total", color="k")
    plt.plot(combined[:, 0], combined[:, 2], label="Nuclear", color="tab:blue")
    plt.plot(combined[:, 0], combined[:, 1], label="Electronic", color="tab:red")
    plt.xlim(np.min(combined[:, 0]), np.max(combined[:, 0]) * 1.05)
    for b in boundaries:
        plt.axvline(b, color="k", ls="--")
    plt.xlabel(r"Depth [$\mu$m]", fontsize=16)
    plt.ylabel(r"Energy loss [keV/nm]", fontsize=16)
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
