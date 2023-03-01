import os
import re
from datetime import datetime

from db_connection import contracts, costs

date = datetime.now()
last_month = date.month - 1
beginning_of_period = datetime(date.year, last_month, 1)

file_path = os.path.join(r"C:\temp", "poh_spec_instr.csv")
assert os.path.exists(
    file_path
), f"File {file_path} does not exist, RUN get.value.of.lis.po"

PO = None


def get_data(file: str):
    global PO
    with open(file, "r") as f:
        rows = f.readlines()

    data = []
    valid_row = re.compile(r"CS.*CAT.*LOT", re.IGNORECASE)
    for row in rows:
        if valid_row.search(row):
            if PO is None:
                PO = row.split(",")[1].replace('"', "").rstrip("\n")

            row = [
                val
                for val in row.split(",")[0].replace('"', "").lstrip(" ").split(" ")
                if val != ""
            ]

            # print(row)

            temp = {
                "quantity": int(row[0].replace(",", "")),
                "item": row[4],
            }

            try:
                temp["lot"] = row[7]
                temp["expiry"] = row[9]
            except IndexError:
                temp["lot"] = "n/a"
                temp["expiry"] = "n/a"

            data.append(temp)

    return data


def get_cost_from_db(item: str):
    doc = costs.find_one(
        {
            "alias": item,
        }
    )

    if not doc:
        return 0

    if doc:
        return doc["cost"]


def calculate_average_price(item: str):
    docs = list(
        contracts.find(
            {
                "contractname": {
                    "$nin": [
                        "HOSPITAL PRICE - 22-10-20",
                        "1-49 PRICE - 22-10-20",
                        "50+ PRICE - 22-10-20",
                    ]
                },
                "contractend": {"$gte": beginning_of_period},
                "pricingagreements.item": item,
            }
        )
    )

    if not docs:
        doc = costs.find_one(
            {
                "alias": item,
            }
        )

        if not doc:
            return 0

        if doc:
            return doc["cost"] * 1.27

    prices = []
    for doc in docs:
        for agreement in doc["pricingagreements"]:
            if agreement["item"] == item:
                prices.append(agreement["price"])

    return sum(prices) / len(prices)


def main():
    import sys

    data = get_data(file_path)

    for item in data:
        item["average_price"] = calculate_average_price(item["item"])
        item["average_value"] = item["average_price"] * item["quantity"]
        item["cost"] = get_cost_from_db(item["item"])
        item["cost_value"] = item["cost"] * item["quantity"]

    total_value = sum([item["average_value"] for item in data])
    total_cost = sum([item["cost_value"] for item in data])

    output_file = f"Avg Value of PO {PO} - {total_value:,.2f}.txt"

    with open(output_file, "w") as sys.stdout:
        for idx, val in enumerate(data):
            print(
                f"{idx + 1}.\tItem {val['item']} \
                    \n\tLot {val['lot']} - Exp {val['expiry']} \
                    \n\t{val['quantity']} CS \
                    \n\t$ {val['average_price']:,.2f} / CS (price/cs on avg) \
                    \n\t$ {val['average_value']:,.2f} (value) \
                    \n\t$ {val['cost']:,.2f} / CS (cost/cs) *not including fees rebates etc* \
                    \n\t$ {val['cost_value']:,.2f} (cost) \
                    \n\t----------------------------------- \
                    \n\t$ {val['average_value'] - val['cost_value']:,.2f} (value - cost) \n"
            )

        print(f"Average value of PO {PO} is\t $ {total_value:,.2f}")
        print(f"Current* cost of PO {PO} is\t $ {total_cost:,.2f}")
        print("---------------------------------------------")
        print(f"Average profit of PO {PO} is\t $ {total_value - total_cost:,.2f}")

        print(f"\n\t\t\t\t\t*{datetime.now():%m-%d-%Y}")


if __name__ == "__main__":
    main()
