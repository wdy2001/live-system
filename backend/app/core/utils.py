def infer_category(repair_type: str) -> str:
    rt = repair_type.lower()
    if rt.startswith("electric") or rt.startswith("elec"):
        return "electric"
    if rt.startswith("water") or rt.startswith("plumb") or "pipe" in rt:
        return "water"
    if rt.startswith("gas"):
        return "gas"
    return "other"
