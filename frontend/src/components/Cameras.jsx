import Camera from './Camera';
import { useEffect, useState } from 'react'
import axios from 'axios';;

const Cameras = ({}) => {
  const [numCams, addCam] = useState(0);
  const [cams, setCams] = useState([])

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/cameras")
      .then(response => setCams(response.data))
      .catch(error => console.error('Error:', error));
  }, []);

  const newCam = () => {
    addCam(numCams + 1)
  }

  return (
    <div>
      {cams.map((cam_config) => <Camera config={cam_config}/>)}
    </div>
  );
}

export default Cameras;
