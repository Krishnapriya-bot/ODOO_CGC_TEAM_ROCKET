# pip install cloudinary

import cloudinary
import os

# Cloudinary Config
cloudinary.config(
    cloud_name="dgtaf4krh",
    api_key="781973345294475",
    api_secret="vURcZBmjM3R_SFHmOoG4M6qVfbE",
    secure=True
)

# Flask Config
DATABASE_URL = 'sqlite:///users.db'  # or use PostgreSQL/MySQL
