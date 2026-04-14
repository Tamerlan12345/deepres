import os
frontend_dist = "/app/frontend/dist"
full_path = "../dist_attack/file.txt"
base_path = os.path.abspath(frontend_dist)
safe_path = os.path.abspath(os.path.join(base_path, full_path))
print("base:", base_path)
print("safe:", safe_path)
try:
    print("common:", os.path.commonpath([base_path, safe_path]))
except Exception as e:
    print(e)
