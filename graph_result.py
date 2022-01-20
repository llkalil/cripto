import matplotlib.pyplot as plt
import pandas as pd

csv_name = 'result.csv'
# Load data
data = pd.read_csv(csv_name)

# Plot
x = range(len(data['EndDateTime']))

plt.plot(x, data['ClosePX'])
plt.xlabel('Transaction')
plt.ylabel('Close')

plt.show()
