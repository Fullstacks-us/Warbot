import json

roi_file = "rois.json"

with open(roi_file, "r") as f:
    rois = json.load(f)

fixed_rois = {}

for key, roi_list in rois.items():
    fixed_rois[key] = []
    for roi in roi_list:
        if len(roi) == 4:
            x1, y1, x2, y2 = map(int, roi)
            x1, x2 = sorted([x1, x2])  # Ensure x1 < x2
            y1, y2 = sorted([y1, y2])  # Ensure y1 < y2
            fixed_rois[key].append([x1, y1, x2, y2])

# Save fixed ROIs back to JSON
with open("rois_fixed.json", "w") as f:
    json.dump(fixed_rois, f, indent=4)

print("✅ Fixed ROIs saved to rois_fixed.json")
