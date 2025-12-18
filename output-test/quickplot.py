import numpy as np
import matplotlib.pyplot as plt


data = np.genfromtxt("combined.dat")

plt.plot(data[:, 0], data[:, 3], color="k")
plt.plot(data[:, 0], data[:, 1], color="r")
plt.plot(data[:, 0], data[:, 2], color="b")

plt.show()
