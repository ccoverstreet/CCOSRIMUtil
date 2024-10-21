if __name__ == "__main__":
    layers = [
        (
            1, 
            srim.SRIMConfig("testfile",
                srim.ELEM_DICT["Au"],
                srim.TargetType.SOLID,
                6.15,
                1,
                [1, 1],
                [srim.ELEM_DICT["Ga"], srim.ELEM_DICT["N"]],
                10,
                946000
            )
        ),
        (
            1, 
            srim.SRIMConfig("testfile",
                srim.ELEM_DICT["Au"],
                srim.TargetType.SOLID,
                3.26,
                1,
                [1, 1],
                [srim.ELEM_DICT["Al"], srim.ELEM_DICT["N"]],
                10,
                946000
            )
        ),
        (
            80, 
            srim.SRIMConfig("testfile",
                srim.ELEM_DICT["Au"],
                srim.TargetType.SOLID,
                3.21,
                1,
                [1, 1],
                [srim.ELEM_DICT["Si"], srim.ELEM_DICT["C"]],
                10,
                946000
            )
        )
    ]


    chunks = []

    boundaries = []

    energy = 0
    prev_x = 0
    for i, layer in enumerate(layers):
        boundaries.append(layer[0] + prev_x)
        print("\n\n\n")
        if i == 0:
            energy = layer[1].max_energy

        print(f"Energy: {energy}")

        layer[1].max_energy = energy
        print(layer[1])
        srim.run_srim_config(layer[1])

        table = srim.convert_srim_to_table(srim.read_srim_output_file(f"srim/testfile"),
                                   srim.ConversionConfig(layer[1].density, 1.0))

        table = table[::-1]

        ind = np.argmax(table[:, 0] > layer[0]) - 1
        #print(table)
        print("Index", ind, table[ind, :])

        depth = layer[0]
        nuclear = np.interp(depth, table[:, 0], table[:, 1])
        electronic = np.interp(depth, table[:, 0], table[:, 2])
        total = np.interp(depth, table[:, 0], table[:, 3])
        boundary_energy = np.interp(depth, table[:, 0], table[:, 4])

        print(depth, nuclear, electronic, total, boundary_energy)

        # Add previous boundary point to all x values
        table[:, 0] = table[:, 0] + prev_x

        # Set for next loop
        energy = boundary_energy
        if ind == -1:
            chunk = table[:, :]
        else:
            chunk = np.vstack((table[:ind + 1, :], np.array([depth + prev_x, nuclear, electronic, total, boundary_energy])))

        print("CHUNK", chunk)
        chunks.append(chunk)


        prev_x += depth


        plt.plot(table[:, 0], table[:, 3], marker="o")
        plt.show()

    print("FINISHED LOOP")
    #print(chunks)
    combined = np.vstack(chunks)
    #print(combined)
    np.savetxt("GaN_AlN_SiC.dat", combined)
    plt.plot(combined[:, 0], combined[:, 3])
    for b in boundaries:
        plt.axvline(b, color="k", ls="--")
    plt.xlim(np.min(combined[:, 0]), np.max(combined[:, 0]))
    plt.show()

