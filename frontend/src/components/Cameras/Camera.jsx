import ReactPlayer from 'react-player/lazy'
import { useEffect, useState } from 'react';

const Camera = ({ id }) => {
  const [playing, setPlaying] = useState(true);
  const [config, setConfig] = useState()
  const [isLoading, setIsLoading] = useState(true);

  // Note: hls.js requires a path based URL. Adding query parameters adds range headers which breaks the functionality.
  const [url, setUrl] = useState('');

  async function waitUntilAvailable() {
    let retries = 0
    const maxRetries = 5
    while (retries < maxRetries) {
      const response = await fetch(`http://localhost:8000/cameras/${id}/ready`)
      if (!response.ok || response.status !== 200) {
        retries++
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
    waitUntilAvailable()
  }, [])

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
        <span>ID: {id}</span>
        <span>Name: {config.name}</span>
        <span>Location: {config.location}</span>
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
              debug: true,
              // One of the commented options below causes buffering issues
              // maxMaxBufferLength: 320,
              // backBufferLength: 300,
              // maxBufferLength: 2,
              // frontBufferFlushThreshold: 2,
              // maxBufferSize: 15,
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
          fetch(`http://localhost:8000/cameras/${id}/`).then(response => response.json())
            .then(camera => {
              setUrl(`http://localhost:8000/${camera.active_playlist}`)
              setPlaying(true)
              setConfig(camera)
            })
        }}
      />
    </div>
  );
}

export default Camera;
