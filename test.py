import json

import pandas as pd

with open("./data/complete_companies.json") as f:
    data = json.load(f)

with open("./data/companies.json") as f:
    organized_data = json.load(f)

final_data = []

for organized_company in organized_data:
    link = organized_company.get("ccs company link")

    for unorganized_company in data:
        if unorganized_company.get("ccs company link") == link:
            final_data.append(unorganized_company)

            data.remove(unorganized_company)

            break

with open("./data/final.json", "w") as f:
    json.dump(final_data, f, indent=4)

df = pd.DataFrame(final_data).drop_duplicates()

df.to_excel("./data/data.xlsx", index=False)

print(len(df))