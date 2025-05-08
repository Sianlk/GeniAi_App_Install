import requests, json
def fetch_land_data(postcode):
    response = requests.get(f"https://api.ordnancesurvey.co.uk/land/v1/{postcode}")
    if response.ok:
        return response.json()
    else:
        return None
def apply_building_rules(land_data):
    return {"height": 10, "setback": 2}
def generate_design_plan(land_data, rules):
    return {"plot_size": land_data.get("plot_size"), "max_height": rules["height"], "setback": rules["setback"], "design_type": "luxury"}
if __name__ == "__main__":
    postcode = "SW1A1AA"
    land_data = fetch_land_data(postcode)
    if land_data:
        rules = apply_building_rules(land_data)
        plan = generate_design_plan(land_data, rules)
        print("Generated Plan:", json.dumps(plan, indent=2))
    else:
        print("Failed to fetch land data.")
