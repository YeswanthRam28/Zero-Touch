import json

# Load frozen outputs
with open("fusion/inputs/vision_output.json") as f:
    vision = json.load(f)
with open("fusion/inputs/voice_output.json") as f:
    voice = json.load(f)

# STEP 2: Time Alignment
time_diff = abs(vision["timestamp"] - voice["timestamp"])
threshold = 1.0  # seconds

if time_diff < threshold:
    print("STEP 2 OK: vision and voice are aligned")
else:
    print("STEP 2 FAILED: not aligned")
# STEP 3: Confidence Normalization
def normalize(value):
    if value > 1:  # assuming 0-100 scale
        return value / 100
    return value  # already 0-1

vision_conf = normalize(vision["confidence"])
voice_conf = normalize(voice["confidence"])

print(f"Normalized vision confidence: {vision_conf}")
print(f"Normalized voice confidence: {voice_conf}")
