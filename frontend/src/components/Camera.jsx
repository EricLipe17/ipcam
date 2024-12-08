import ReactPlayer from 'react-player/lazy'
import { useState } from 'react';
import axios from 'axios';

const Camera = ({config}) => {
  const [playing, setPlaying] = useState(true);
  const [url, setUrl] = useState(`http://127.0.0.1:8000/${config.active_playlist}`);

  return (
    <div>
      <ReactPlayer
        url={url}
        playing={playing}
        controls
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => {
          // Use this to get the next playlist to continue the livestream
          axios.get(`http://127.0.0.1:8000/cameras/${config.id}/`).then(response => {
            const camera = response.data
            console.log(camera.active_playlist)
            setUrl(`http://127.0.0.1:8000/${camera.active_playlist}`)
            setPlaying(true)
          })
        }}
      />
    </div>
  );
}

export default Camera;
