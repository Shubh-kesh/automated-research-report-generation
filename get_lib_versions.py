import importlib.metadata

req_file = "requirements.txt"

with open(req_file, "r") as f:
    packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

updated_lines = []

for pkg in packages:
    # If version already pinned, extract only package name
    if "==" in pkg:
        name = pkg.split("==")[0].strip()
    else:
        name = pkg.strip()

    try:
        version = importlib.metadata.version(name)
        updated_lines.append(f"{name}=={version}")
    except importlib.metadata.PackageNotFoundError:
        # Keep as is if not installed
        updated_lines.append(pkg)
        print(f"⚠️ {name} not installed, keeping original entry")

# Write back updated requirements.txt
with open(req_file, "w") as f:
    f.write("\n".join(updated_lines) + "\n")

print("✅ requirements.txt updated with installed versions")