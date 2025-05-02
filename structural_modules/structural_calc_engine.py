import math

# Example material strengths (MPa)
MATERIALS = {
    "concrete": 25,
    "steel": 250,
    "timber": 12
}

# Calculate load (simplified)
def calculate_load(area_m2, live_load_kN_m2, dead_load_kN_m2):
    total_load = area_m2 * (live_load_kN_m2 + dead_load_kN_m2)
    return total_load

# Check material suitability
def check_material(material, load_kN, area_m2):
    strength = MATERIALS.get(material)
    if not strength:
        return False
    stress = load_kN / area_m2
    return stress <= strength

# Apply UK Building Regs (Part A Example)
def apply_building_regs():
    # Example: max height, fire escape width, insulation R-values, etc.
    regs = {
        "max_height_m": 11,
        "fire_escape_min_width_m": 0.9,
        "min_roof_insulation_r_value": 5.0
    }
    return regs

if __name__ == "__main__":
    area = 100  # m²
    total_load = calculate_load(area, live_load_kN_m2=3, dead_load_kN_m2=2)
    print(f"Total Load on {area}m²: {total_load} kN")

    material_ok = check_material("concrete", total_load, area)
    print(f"Concrete Suitable? {'Yes' if material_ok else 'No'}")

    regs = apply_building_regs()
    print("Applied Building Regulations:", regs)
