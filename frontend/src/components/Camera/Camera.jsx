import ReactPlayer from 'react-player/lazy'
import { useEffect, useRef, useState } from 'react';
import Error from '../Errors/Error';
import LoadingSpinner from '../LoadingSpinner/LoadingSpinner';

const Camera = ({ id }) => {
  const [playing, setPlaying] = useState(true);
  const [config, setConfig] = useState()
  const [retries, setRetries] = useState(0)
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("")
  const playerRef = useRef()

  // Note: hls.js requires a path based URL. Adding query parameters adds range headers which breaks the functionality.
  const [url, setUrl] = useState('');

  useEffect(() => {
    async function fetchStream(retries) {
      if (retries < 10) {
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
    return <LoadingSpinner />
  }

  return (
    <div className="w-fit h-fit">
      {errorMsg !== "" ? (
        <Error errorMsg={errorMsg} />
      ) :
        (
          <>
            <div className="flex space-x-5 bg-black border border-white">
              <span>ID: {id}</span>
              <span>Name: {config.name}</span>
              {config.location && <span>Location: {config.location}</span>}
            </div>
            <ReactPlayer
              className="w-fit h-fit"
              ref={playerRef}
              url={url}
              playing={playing}
              controls
              volume={0}
              muted={true}
              config={{
                file: {
                  hlsOptions: {
                    liveSyncDurationCount: 1,
                    maxBufferLength: 30,
                    maxMaxBufferLength: 30,
                    backBufferLength: 0,
                    frontBufferFlushThreshold: 30,
                    maxBufferSize: 10 // MB
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
