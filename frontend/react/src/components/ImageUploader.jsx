import React, { useState } from 'react';
import axios from 'axios';

const ImageUploader = () => {
  const [userId, setUserId] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imageUrl, setImageUrl] = useState('');

  const handleUpload = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('image', imageFile);

    try {
      const res = await axios.post('http://localhost:5000/upload', formData);
      setImageUrl(res.data.image_url);
    } catch (error) {
      alert('Upload failed!');
      console.error(error);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Upload an Image</h2>
      <form onSubmit={handleUpload}>
        <input
          type="text"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          required
        />
        <br /><br />
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setImageFile(e.target.files[0])}
          required
        />
        <br /><br />
        <button type="submit">Upload</button>
      </form>

      {imageUrl && (
        <div style={{ marginTop: '20px' }}>
          <h4>Uploaded Image:</h4>
          <img src={imageUrl} alt="Uploaded" width="300" />
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
