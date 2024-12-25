import ReactPlayer from 'react-player/lazy'
import { useEffect, useState } from 'react';

const Camera = ({ cameraConfig }) => {
  const [playing, setPlaying] = useState(true);
  const [config, setConfig] = useState(cameraConfig)
  const [url, setUrl] = useState(`http://localhost:8000/${config.active_playlist}`);
  const [isLoading, setIsLoading] = useState(true);

  async function fetchCameraUntilReady(config) {
    let retries = 0
    let maxRetries = 5
    while (retries < maxRetries) {
      const response = await fetch(`http://localhost:8000/cameras/${config.id}/ready`)
      if (!response.ok || response.status !== 200) {
        retries++
        await new Promise(resolve => setTimeout(resolve, 4000))
      } else {
        const camera = await response.json()
        setConfig(camera)
        setUrl(`http://localhost:8000/${camera.active_playlist}`)
        setIsLoading(false)
        break
      }
    }
    // TODO: Add error handling if we hit max retries
  }

  useEffect(() => {
    if (config.active_playlist === null) {
      fetchCameraUntilReady(config)
    }
    else {
      setIsLoading(false)
    }
  })

  if (isLoading) {
    return <div>Loading Stream...</div>
  }

  return (
    <div>
      <ReactPlayer
        url={url}
        playing={playing}
        controls
        volume={0}
        muted={true}
        onStart={() => {
          console.log("In onStart.")
        }}
        onReady={() => {
          console.log("In onReady.")
        }}
        onError={(e) => {
          console.log(`In onError: ${JSON.stringify(e, null, 4)}`)
        }}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => {
          // Use this to get the next playlist to continue the livestream
          fetch(`http://localhost:8000/cameras/${cameraConfig.id}/`).then(response => response.json())
            .then(camera => {
              setUrl(`http://localhost:8000/${camera.active_playlist}`)
              setPlaying(true)
            })
        }}
      />
    </div>
  );
}

export default Camera;
