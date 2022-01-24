import csv

import matplotlib.pyplot as plt
import pandas as pd

csv_name = 'app/cashbook.csv'
# Load data
data = pd.read_csv(csv_name)

# Plot
x = range(len(data['EndDateTime']))

plt.plot(x, data['ClosePX'])
plt.xlabel('Transaction')
plt.ylabel('Close')
points_y_s = []
points_x_s = []
points_y_b = []
points_x_b = []
with open(csv_name, newline='') as f:
    reader = csv.reader(f)
    i = 0
    for row in reader:
        if i != 0:
            if row[10] == "BUY":
                points_y_b.append(i - 1)
                points_x_b.append(float(row[4]))
            else:
                points_y_s.append(i - 1)
                points_x_s.append(float(row[4]))
        i = i + 1

plt.scatter(points_y_b, points_x_b, color='green')
plt.scatter(points_y_s, points_x_s, color='red')
plt.show()
