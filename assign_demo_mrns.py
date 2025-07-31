import pandas as pd
import numpy as np

# 1) Load your cleaned demographics (200 patients) and the full variant CSV
demo_df     = pd.read_csv("clean_demographics.csv")
variants_df = pd.read_csv("TSO500_Synthetic_Final.csv")  # this should be all ~2000+ rows

# 2) Sample 50 patient MRNs
np.random.seed(42)
sampled_mrns = demo_df["mrn"].sample(n=50).tolist()

# 3) Overwrite every variant’s MRN, but keep all rows
variants_df["MRN"] = np.random.choice(sampled_mrns, size=len(variants_df))

# 4) Save back (in place or new file)
variants_df.to_csv("TSO500_Synthetic_Final.csv", index=False)
print(f"✅ Replaced MRNs and wrote {len(variants_df)} rows")
