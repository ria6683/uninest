import os

# Create requirements.txt (list of software the server needs)
os.system("pip freeze > requirements.txt")
print("✅ Created requirements.txt")

# Update settings.py to allow the website to run anywhere
settings_path = 'melbourne_rentals/settings.py'
with open(settings_path, 'r') as f:
    content = f.read()

# Change ALLOWED_HOSTS to allow all (safe for beginner deployment)
if "ALLOWED_HOSTS = ['*']" not in content:
    content = content.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = ['*']")
    # In case you already have the mac setup from before
    content = content.replace("ALLOWED_HOSTS = ['*']", "ALLOWED_HOSTS = ['*', '.pythonanywhere.com']")
    
    # Add a setting so uploaded images work on the live server
    if "STATIC_ROOT" not in content:
        content += "\nSTATIC_ROOT = BASE_DIR / 'staticfiles'\n"
    
    with open(settings_path, 'w') as f:
        f.write(content)
    print("✅ Updated settings.py for deployment")
else:
    print("ℹ️ Settings already configured.")
