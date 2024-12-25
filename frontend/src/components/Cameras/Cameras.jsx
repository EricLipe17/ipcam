import AddCameraModal from './AddCameraModal';
import Camera from './Camera';
import { useEffect, useState } from 'react'

const Cameras = () => {
  const [cameras, setCameras] = useState([])
  const [camAdded, setCamAdded] = useState(false)

  useEffect(() => {
    const fetchCameras = () => {
      fetch("http://localhost:8000/cameras/").then(response => response.json())
        .then(cameras => setCameras(cameras))
        .catch(error => console.error('Error:', error));
    }
    fetchCameras()
  }, [camAdded]);

  return (
    <div>
      <AddCameraModal setCamAdded={setCamAdded} />
      <br />
      {cameras.map((cameraConfig) => {
        return (
          <Camera cameraConfig={cameraConfig} />
        )
      })}
    </div>
  );
}

export default Cameras;
