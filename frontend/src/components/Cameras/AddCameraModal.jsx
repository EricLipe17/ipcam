import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AddCameraModal({ showModal, handleModal }) {
  const [errors, setErrors] = useState({});
  const [addError, setAddError] = useState("");
  const [inputs, setInputs] = useState({
    name: '',
    url: '',
    location: '', // Optional
    transcode: false, // Optional
  });
  const navigate = useNavigate();
  const checkBoxName = "transcode"

  const handleClose = () => {
    handleModal(false)
  };

  const handleChange = (event) => {
    if (event.target.name === checkBoxName) {
      setInputs({
        ...inputs,
        [event.target.name]: event.target.checked,
      });
    } else {
      setInputs({
        ...inputs,
        [event.target.name]: event.target.value,
      });
    }
  };

  const isValid = () => {
    let newErrors = {};

    if (!inputs.name) {
      newErrors.name = 'Camera name is required';
    }

    if (!inputs.url) {
      newErrors.url = 'RTSP Url is required';
    } else {
      try {
        const parsedUrl = new URL(inputs.url)
        if (parsedUrl.protocol !== 'rtsp:' || parsedUrl.hostname === '' || parsedUrl.port === '') {
          newErrors.url = 'Invalid RTSP Url format';
        }
      } catch (error) {
        newErrors.url = 'Invalid RTSP Url format';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  const handleAdd = async (event) => {
    if (isValid()) {
      const response = await fetch('http://localhost:8000/cameras/add_camera', {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(inputs),
      })
      if (!response.ok) {
        setAddError("Encountered error trying to add camera.")
        event.preventDefault()
        return false
      }

      handleModal(false)
      // TODO: the navigate only re-renders the Cameras component if the URL changes. If we are already on the cameras page, we need to force a re-render.
      navigate('/cameras')
      return true
    } else {
      event.preventDefault();
      return false;
    }
  };

  return (
    <div>
      {showModal && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-black border border-gray-700 rounded-lg p-6 z-50 w-1/2">
            <h2 className="text-gold mb-4">Add Camera</h2>
            <label className="block text-gold  mb-2">
              Name:
              <input
                type="text"
                name="name"
                value={inputs.name}
                onChange={handleChange}
                className="block w-full p-2 mt-1 bg-black border border-gray-700 rounded text-white"
              />
              {errors.name && <span className="text-red-500">{errors.name}</span>}
            </label>
            <label className="block text-gold  mb-2">
              RTSP Url:
              <input
                type="text"
                name="url"
                value={inputs.url}
                onChange={handleChange}
                className="block w-full p-2 mt-1 bg-black border border-gray-700 rounded text-white"
              />
              {errors.url && <span className="text-red-500">{errors.url}</span>}
            </label>
            <label className="block text-gold  mb-2">
              Location:
              <input
                type="text"
                name="location"
                value={inputs.location}
                onChange={handleChange}
                className="block w-full p-2 mt-1 bg-black border border-gray-700 rounded text-white"
              />
            </label>
            <label className="block text-gold  mb-4">
              Transcode:
              <input
                type="checkbox"
                name="transcode"
                checked={inputs.transcode}
                onChange={handleChange}
                className="ml-2"
              />
            </label>
            <div className="flex justify-end">
              <button
                onClick={handleAdd}
                className="bg-gold text-black py-2 px-4 rounded hover:bg-white hover:text-black transition duration-300 mr-2"
              >
                Add
              </button>
              <button
                onClick={handleClose}
                className="bg-gold text-black py-2 px-4 rounded hover:bg-white hover:text-black transition duration-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AddCameraModal