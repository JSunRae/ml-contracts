import pandas as pd, pathlib
p = pathlib.Path(__file__).parent
df = pd.read_csv(p/"l2_fixture.csv", parse_dates=["ts_utc"])
df.to_parquet(p/"l2_fixture.parquet", index=False)
print(p/"l2_fixture.parquet")
