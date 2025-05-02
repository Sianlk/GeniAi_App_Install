MATERIALS = {"concrete": 25, "steel": 250, "timber": 12}
def calculate_load(area, live_load, dead_load):
    return area * (live_load + dead_load)
def check_material(material, load, area):
    return (load / area) <= MATERIALS.get(material, 0)
def apply_building_regs():
    return {"max_height_m": 11, "fire_escape_min_width_m": 0.9, "min_roof_insulation_r_value": 5.0}
if __name__ == "__main__":
    area = 100
    total_load = calculate_load(area, 3, 2)
    print(f"Total Load on {area}m²: {total_load} kN")
    material_ok = check_material("concrete", total_load, area)
    print(f"Concrete Suitable? {'Yes' if material_ok else 'No'}")
    print("Building Regs:", apply_building_regs())
