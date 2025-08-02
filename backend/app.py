# pip install flask 

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import cloudinary.uploader
from models import Base, UserImage
import config

app = Flask(__name__)
CORS(app)  # Allow CORS for React frontend

# Set up DB
engine = create_engine(config.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@app.route('/upload', methods=['POST'])
def upload_image():
    session = Session()

    user_id = request.form.get('user_id')
    image = request.files.get('image')

    if not user_id or not image:
        return jsonify({"error": "Missing user_id or image"}), 400

    # Upload to Cloudinary
    result = cloudinary.uploader.upload(image)

    image_record = UserImage(
        user_id=int(user_id),
        image_url=result['secure_url'],
        public_id=result['public_id']
    )

    session.add(image_record)
    session.commit()
    session.close()

    return jsonify({
        "message": "Image uploaded successfully",
        "image_url": result['secure_url']
    })

if __name__ == '__main__':
    app.run(debug=True)
