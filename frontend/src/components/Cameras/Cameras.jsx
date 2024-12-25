import AddCameraModal from './AddCameraModal';
import Camera from './Camera';
import { useEffect, useState } from 'react'

const Cameras = () => {
  const [cameras, setCameras] = useState([])
  const [camAdded, setCamAdded] = useState(false)

  useEffect(() => {
    const fetchCameras = () => {
      fetch("http://127.0.0.1:8000/cameras/").then(response => response.json())
        .then(cameras => setCameras(cameras))
        .catch(error => console.error('Error:', error));
    }
    fetchCameras()
  }, [camAdded]);

  return (
    <div>
      <AddCameraModal setCamAdded={setCamAdded} />
      <br />
      {cameras.map((cam_config) => <Camera config={cam_config} />)}
    </div>
  );
}

export default Cameras;
