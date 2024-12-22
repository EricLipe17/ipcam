import AddCameraModal from './AddCameraModal';
import Camera from './Camera';
import { useEffect, useState } from 'react'

const Cameras = () => {
  const [cams, setCams] = useState([])

  useEffect(() => {
    fetch("http://127.0.0.1:8000/cameras/")
      .then(response => response.json())
      .then(data => setCams(data))
      .catch(error => console.error('Error:', error));
  }, []);

  return (
    <div>
      <AddCameraModal cameras={cams} setCameras={setCams} />
      <br />
      {cams.map((cam_config) => <Camera config={cam_config} />)}
    </div>
  );
}

export default Cameras;
