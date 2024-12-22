import React, { useState } from 'react';
import ReactModal from 'react-modal';
import { useNavigate } from "react-router-dom";

function AddCameraModal({ cameras, setCameras }) {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [errors, setErrors] = useState({});
  const [addError, setAddError] = useState("");
  const [inputs, setInputs] = useState({
    name: '',
    url: '',
    location: '', // Optional
  });

  const handleShowModal = () => {
    setShowModal(true);
  };

  const handleHideModal = () => {
    setShowModal(false);
  };

  const handleChange = (event) => {
    setInputs({
      ...inputs,
      [event.target.name]: event.target.value,
    });
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
      console.log("Making request")
      const response = await fetch('http://localhost:8000/cameras/add_camera', {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(inputs),
      })
      if (!response.ok) {
        console.log(response)
        setAddError(response)
        event.preventDefault()
        return false
      }
      const camera = await response.json()
      cameras.push(camera)
      setShowModal(false)
      setCameras(cameras)
      return true
    } else {
      event.preventDefault();
      return false;
    }
  };

  const customStyles = {
    content: {
      top: '35%',
      left: '50%',
      right: 'auto',
      bottom: 'auto',
      marginRight: '-50%',
      width: '60%',
      transform: 'translate(-40%, -10%)',
    },
  };

  return (
    <div>
      <button onClick={handleShowModal}>Add Camera</button>

      <ReactModal isOpen={showModal} onRequestClose={handleHideModal} ariaHideApp={false} style={customStyles}>
        <h2>Add Camera</h2>
        <label>
          Name:
          <input type="text" name="name" value={inputs.name} onChange={handleChange} />
          {errors.name && <span className="error">{errors.name}</span>}
        </label>
        <br />
        <label>
          RTSP Url:
          <input type="text" name="url" value={inputs.url} onChange={handleChange} />
          {errors.url && <span className="error">{errors.url}</span>}
        </label>
        <br />
        <label>
          Location:
          <input type="text" name="location" value={inputs.location} onChange={handleChange} />
        </label>
        <br />
        <button type="submit" onClick={handleAdd}>Add</button>
        {addError && <span className="error">{addError}</span>}
      </ReactModal>
    </div>
  );
}

export default AddCameraModal