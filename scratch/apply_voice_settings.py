import sys
sys.path.insert(0, r"c:\Users\mones\OneDrive\Desktop\Vikram AI")

from backend.database.sqlite import db

# Set deep voice and maximum volume in database
db.set_setting("voice_name", "Microsoft David Desktop")
db.set_setting("voice_pitch", "-6st")
db.set_setting("voice_speed", "-1")
db.set_setting("voice_volume", "100")

print("Database voice settings updated:")
print("voice_name:", db.get_setting("voice_name"))
print("voice_pitch:", db.get_setting("voice_pitch"))
print("voice_speed:", db.get_setting("voice_speed"))
print("voice_volume:", db.get_setting("voice_volume"))
