import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# This is the CSV data as a string (replace with file reading if needed)
csv_data = """benchmark,run,result
quadratic,baseline,785
quadratic,lvn,502
primes-between,baseline,574100
primes-between,lvn,571439
birthday,baseline,484
birthday,lvn,257
orders,baseline,5352
orders,lvn,5352
sum-check,baseline,5018
sum-check,lvn,5018
palindrome,baseline,298
palindrome,lvn,298
totient,baseline,253
totient,lvn,253
relative-primes,baseline,1923
relative-primes,lvn,1173
hanoi,baseline,99
hanoi,lvn,99
is-decreasing,baseline,127
is-decreasing,lvn,119
check-primes,baseline,8468
check-primes,lvn,4985
sum-sq-diff,baseline,3038
sum-sq-diff,lvn,1724
fitsinside,baseline,10
fitsinside,lvn,10
fact,baseline,229
fact,lvn,167
loopfact,baseline,116
loopfact,lvn,82
recfact,baseline,104
recfact,lvn,78
factors,baseline,72
factors,lvn,72
perfect,baseline,232
perfect,lvn,232
bitshift,baseline,167
bitshift,lvn,103
digital-root,baseline,247
digital-root,lvn,247
up-arrow,baseline,252
up-arrow,lvn,252
sum-divisors,baseline,159
sum-divisors,lvn,159
ackermann,baseline,1464231
ackermann,lvn,1464231
pythagorean_triple,baseline,61518
pythagorean_triple,lvn,61518
euclid,baseline,563
euclid,lvn,374
binary-fmt,baseline,100
binary-fmt,lvn,100
lcm,baseline,2326
lcm,lvn,2326
gcd,baseline,46
gcd,lvn,46
catalan,baseline,659378
catalan,lvn,659378
armstrong,baseline,133
armstrong,lvn,130
pascals-row,baseline,146
pascals-row,lvn,83
collatz,baseline,169
collatz,lvn,169
sum-bits,baseline,73
sum-bits,lvn,73
rectangles-area-difference,baseline,14
rectangles-area-difference,lvn,14
mod_inv,baseline,558
mod_inv,lvn,307
karatsuba,baseline,1548
karatsuba,lvn,1446
reverse,baseline,46
reverse,lvn,43
fizz-buzz,baseline,3652
fizz-buzz,lvn,2257
bitwise-ops,baseline,1690
bitwise-ops,lvn,1689"""

# Parse the CSV data
import io
df = pd.read_csv(io.StringIO(csv_data))

# Reshape the data for easier plotting
pivot_df = df.pivot(index='benchmark', columns='run', values='result')

# Calculate improvement percentage
pivot_df['improvement'] = (pivot_df['baseline'] - pivot_df['lvn']) / pivot_df['baseline'] * 100

# Sort by improvement percentage
pivot_df = pivot_df.sort_values('improvement', ascending=False)

# Filter out benchmarks with very large values to keep the plot readable
# and focus on benchmarks with noticeable differences
small_benchmarks = pivot_df[pivot_df['baseline'] < 10000].copy()

# Create the plot
plt.figure(figsize=(14, 10))

# Set up bar positions
benchmarks = small_benchmarks.index
x = np.arange(len(benchmarks))
width = 0.35

# Create bars
baseline_bars = plt.bar(x - width/2, small_benchmarks['baseline'], width, label='Baseline', color='skyblue')
lvn_bars = plt.bar(x + width/2, small_benchmarks['lvn'], width, label='LVN', color='lightgreen')

# Customize the plot
plt.xlabel('Benchmark')
plt.ylabel('Result Value')
plt.title('LVN+TDCE Optimization Results')
plt.xticks(x, benchmarks, rotation=90)
plt.legend()

# Add percentage improvement as text above bars
for i, benchmark in enumerate(benchmarks):
    improvement = small_benchmarks.loc[benchmark, 'improvement']
    if improvement > 0:  # Only show text for actual improvements
        plt.text(i, small_benchmarks.loc[benchmark, 'baseline'], 
                 f'{improvement:.1f}%', 
                 ha='center', va='bottom', rotation=0,
                 fontsize=8, color='green')

plt.tight_layout()

# Create a second plot for improvement percentages
plt.figure(figsize=(14, 8))
improved = pivot_df[pivot_df['improvement'] > 0].copy()
plt.bar(improved.index, improved['improvement'], color='green')
plt.xlabel('Benchmark')
plt.ylabel('Improvement Percentage (%)')
plt.title('LVN Optimization Improvement Percentage')
plt.xticks(rotation=90)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Save the plots
plt.savefig('lvn_comparison.png')
plt.savefig('lvn_improvement.png')

print("Plots saved as 'lvn_comparison.png' and 'lvn_improvement.png'")
plt.show()