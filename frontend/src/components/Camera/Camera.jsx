import ReactPlayer from 'react-player/lazy'
import { useEffect, useState } from 'react';

const Camera = ({ id }) => {
  const [playing, setPlaying] = useState(true);
  const [config, setConfig] = useState()
  const [retries, setRetries] = useState(0)
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("")

  // Note: hls.js requires a path based URL. Adding query parameters adds range headers which breaks the functionality.
  const [url, setUrl] = useState('');

  useEffect(() => {
    async function fetchStream(retries) {
      if (retries < 1) {
        try {
          const response = await fetch(`http://localhost:8000/cameras/${id}/ready`)
          if (response.status === 200) {
            const camera = await response.json()
            setConfig(camera)
            setUrl(`http://localhost:8000/${camera.active_playlist}`)
            setIsLoading(false)
          } else {
            setRetries(retries + 1)
          }
        } catch (err) {
          setIsLoading(false)
          setErrorMsg(`Error trying to query cammera livestream 'ready' endpoint. Error: ${JSON.stringify(err)}`)
          setRetries(9999)
        }
      } else {
        setIsLoading(false)
        setErrorMsg("Unable to load the camera's livestream. Try refreshing the page! If the problem persists, check whether the camera's data is being recorded in ${THE_STORAGE_DIR}.")
      }
    }
    const timeoutID = setTimeout(fetchStream, 2000, retries)
    return () => clearTimeout(timeoutID)
  }, [id, retries])

  if (isLoading) {
    return <div>Loading Stream...</div>
  }

  return (
    <div>
      {errorMsg !== "" ? (<div style={{ color: "red", }}>{errorMsg}</div>) :
        (
          <>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              background: "black",
              border: "2px solid white",
            }}>
              <span>ID: {id}</span>
              <span>Name: {config.name}</span>
              {config.location && <span>Location: {config.location}</span>}
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
                setIsLoading(true)
                // Use this to get the next playlist to continue the livestream
                fetch(`http://localhost:8000/cameras/${id}/`).then(response => response.json())
                  .then(camera => {
                    setUrl(`http://localhost:8000/${camera.active_playlist}`)
                    setPlaying(true)
                    setConfig(camera)
                    setIsLoading(false)
                  })
              }}
            />
          </>
        )
      }
    </div >
  );
}

export default Camera;
