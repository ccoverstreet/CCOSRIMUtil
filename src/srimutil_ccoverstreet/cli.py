def cli_main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="CCO SRIM Utils",
        description="Use to convert SRIM stopping tables output to a energy loss plot",
    )

    parser.add_argument("datafile")
    parser.add_argument("-s", "--save", type=str,
                        help="Save the converted depth and energy loss data to a file. Filename should not have spaces (unless within quotes).", default="")
    parser.add_argument("-r", "--rho", type=float, required=True,
                        help="theoretical density of material (ex. 3.43 g/cm^3)")
    parser.add_argument("-p", "--packing", type=float, required=True,
                        help="estimated packing fraction of material (ex. 0.8)")

    args = parser.parse_args()

    proc_config = ProcessConfig(args.datafile, args.save, args.rho, args.packing)
    process_file(proc_config)

def process_file(proc_config):
    filename = proc_config.srim_file
    rho = proc_config.rho
    packing_frac = proc_config.packing
    srim_file = proc_config.srim_file
    output_file = proc_config.output_file

    print(f"Processing {filename}")

    srim_data = read_srim_output(srim_file)
    data = srim_data.data

    print(f"Using density of {rho} g/cm^3")
    print(f"SRIM was run using density of {srim_data.rho} g/cm^3")
    print(f"Using packing fraction of {packing_frac}")

    # Perform all conversions to usable output format
    # We use the SRIM density and user provided density to properly scale 
    # the data.
    # Density correction rho_corr = user_rho / SRIM_rho
    rho_corr = rho / srim_data.rho

    energies = data[:, 0]
    depth = range_to_depth(data[:, 3]) / packing_frac / rho_corr
    elec_dedx = dedx_to_kev_nm(data[:,1]) * rho_corr
    nuclear_dedx = dedx_to_kev_nm(data[:, 2]) * rho_corr
    total_dedx = elec_dedx + nuclear_dedx


    # Calculate dx(dE/dx) for caculating stopping depth
    # Using typical finite derivative formula
    dx_depth = np.diff(depth) / 2 + depth[:-1]
    dx_total_dedx = np.diff(total_dedx) / np.diff(depth)

    dxdedx_cutoff = find_index_before_stopping(dx_depth, dx_total_dedx)


    # Select stopping depth from d/dx(dE/dx)
    global fig, coord
    fig = plt.figure()
    coord = np.array([0, 0])
    def onclick(event):
        global coord, fig
        ax = fig.gca()
        if len(ax.lines) != 1:
            lines = ax.get_lines().pop(1).remove()
            #ax.get_lines().remove(id(lines[0]))

        coord = np.array([event.xdata, event.ydata])

        print(f"Current stopping depth: {event.xdata}")
        ax.axvline(event.xdata)
        fig.canvas.draw()



    plt.title("Select stopping depth by clicking the graph\nClose this window when finished", fontsize=12)
    plt.plot(dx_depth[dxdedx_cutoff:], dx_total_dedx[dxdedx_cutoff:])
    plt.ylabel("d/dx(dE/dx)")
    plt.xlabel(r"Depth ($\mu$m)")
    #plt.ylim(-3, 2)


    fig.canvas.mpl_connect("button_press_event", onclick)
    plt.show()

    print(f"\nGraphically selected stopping depth: {coord[0]} microns")
    print(f"Maximum stopping distance: {np.max(depth)} microns")

    # Calculate 10% deviation in energy loss
    starting_dedx = total_dedx[-1]
    coord_10p = 0
    for i in range(len(depth)-1, 0, -1):
        pdiff = np.abs((total_dedx[i] - starting_dedx) / (starting_dedx))
        #print(pdiff)
        if pdiff > 0.1:
            coord_10p = depth[i]
            break

    print(f"Stopping depth at 10% deviation: {coord_10p}")


    if len(output_file) > 0:
        combined_array = np.vstack((depth,
                                    elec_dedx, nuclear_dedx, elec_dedx + nuclear_dedx, energies)).T
        with open(output_file, "w") as f:
            np.savetxt(f, np.flip(combined_array, axis=0),
                       header="Depth (um), Electronic Energy Loss (keV/nm), Nuclear Energy Loss (keV/nm), Total Energy Loss (keV/nm), Energy (keV)",
                       delimiter=",")


    # Make plot using selected and calculated stopping depths
    plt.figure()
    plt.plot(depth, total_dedx, label="total", color="k")
    plt.axvline(coord[0], label=f"Graphical stopping: {round(coord[0], 2)} " + r"$\mu$m", color="g")
    plt.axvline(coord_10p, label=f"10% dev. stopping: {round(coord_10p, 2)} " + r"$\mu$m", color="c")
    plt.xlabel(r"Depth ($\mu m$)", fontsize=14)
    plt.ylabel("Energy loss (keV/nm)", fontsize=14)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.legend()
    plt.tight_layout()

    # Create figures using the generated data
    plt.figure()
    plt.plot(depth, elec_dedx + nuclear_dedx,
             label="total", linewidth=1, color="k")
    plt.plot(depth, elec_dedx,
             label="electronic", linewidth=1, color="r", ls="--")
    plt.plot(depth, nuclear_dedx,
             label="nuclear", linewidth=1, color="b", ls="--")
    plt.title(f"{filename}", fontsize=16)
    plt.xlabel(r"Depth ($\mu m$)", fontsize=14)
    plt.ylabel("Energy loss (keV/nm)", fontsize=14)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.legend(fontsize=14)

    plt.tight_layout()


    plt.figure()        
    plt.plot(energies, total_dedx)
    plt.xlabel(r"Energy (keV)", fontsize=14)
    plt.ylabel("dE/dx (keV/nm)", fontsize=14)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.xscale("log")
    plt.tight_layout()


    plt.figure()        
    plt.plot(depth, energies)
    plt.xlabel(r"Depth ($\mu m$)", fontsize=14)
    plt.ylabel("Energy (keV)", fontsize=14)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    plt.show()






if __name__ == "__main__":
    import sys

    print("You may run again with '--help' as an argument to see additional options")
    cli_main()

