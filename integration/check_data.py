
import pandas as pd

df = pd.read_csv('Range_Wise_Integration_Tracker (1).csv', low_memory=False)

print("CSV Column mapping:")
print(f"  CSV: 'Integration Date' → DB: 'integration_date'")
print(f"  CSV: 'CIRCLE' → DB: 'circle'")
print(f"  CSV: 'OEM' → DB: 'oem'")

print(f"\nTotal records in CSV: {len(df)}")
print(f"\nDate range in CSV:")
print(f"  Min: {df['Integration Date'].min()}")
print(f"  Max: {df['Integration Date'].max()}")

print(f"\nCircles in CSV:")
print(df['CIRCLE'].value_counts().head(10))

print(f"\nSample date values:")
print(df['Integration Date'].head(10).tolist())

# Check specific date
sep_12 = df[df['Integration Date'].str.contains('2025-09-12', na=False)]
print(f"\n2025-09-12 records in CSV: {len(sep_12)}")

sep_range = df[(df['Integration Date'] >= '2025-09-12') & (df['Integration Date'] <= '2025-09-15')]
print(f"2025-09-12 to 2025-09-15 records: {len(sep_range)}")

# Check AP circle
ap_records = df[df['CIRCLE'] == 'AP']
print(f"\nAP circle records: {len(ap_records)}")

ap_sep = df[(df['CIRCLE'] == 'AP') & (df['Integration Date'] >= '2025-09-12') & (df['Integration Date'] <= '2025-09-15')]
print(f"AP circle 2025-09-12 to 2025-09-15: {len(ap_sep)}")
