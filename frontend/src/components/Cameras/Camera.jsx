import ReactPlayer from 'react-player/lazy'
import { useEffect, useState } from 'react';

const Camera = ({ cameraConfig }) => {
  const [playing, setPlaying] = useState(true);
  const [config, setConfig] = useState(cameraConfig)
  const [isLoading, setIsLoading] = useState(false);


  // Note: hls.js requires a path based URL. Adding query parameters adds range headers which breaks the functionality.
  const [url, setUrl] = useState(`http://localhost:8000/${config.active_playlist}`);

  async function fetchCameraUntilReady(config) {
    let retries = 0
    let maxRetries = 5
    while (retries < maxRetries) {
      const response = await fetch(`http://localhost:8000/cameras/${config.id}/ready`)
      if (!response.ok || response.status !== 200) {
        retries++
        setIsLoading(true)
        await new Promise(resolve => setTimeout(resolve, 6000))
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
  })

  if (isLoading) {
    return <div>Loading Stream...</div>
  }

  return (
    <div>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        background: "black",
        border: "2px solid white",
      }}>
        <span>ID: {cameraConfig.id}</span>
        <span>Name: {cameraConfig.name}</span>
        <span>Location: {cameraConfig.location}</span>
      </div>
      <ReactPlayer
        url={url}
        playing={playing}
        controls
        volume={0}
        muted={true}
        config={{
          file: {
            hlsOptions: {
              liveSyncDurationCount: 1,
              maxMaxBufferLength: 320,
              backBufferLength: 300,
              maxBufferLength: 2,
              frontBufferFlushThreshold: 2,
              maxBufferSize: 15,
              debug: true
            }
          }
        }}
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
