import json
import numpy as np
import matplotlib.pyplot as plt

proj = json.loads(open("test.json").read())

combined = np.array(proj["result"]["combined"])

plt.plot(combined[:, 0], combined[:, 3])

bounds = proj["result"]["boundaries"]
for i, b in enumerate(bounds):

    plt.axvline(b, color="k", ls="--")
    y_pos = np.max(combined[:, 3]) / 2

    print(bounds, b/2, y_pos)
    if i == 0:
        plt.annotate(proj["layers"][i]["name"], (b / 2, y_pos), ha="center")
    else:
        plt.annotate(proj["layers"][i]["name"], ((bounds[i] + bounds[i-1])/ 2, y_pos), ha="center")


plt.ylim(0, np.max(combined[:, 3]) * 1.05)
plt.show()
