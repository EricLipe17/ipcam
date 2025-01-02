import ReactPlayer from 'react-player/lazy'
import { useEffect, useRef, useState } from 'react';

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
        <div className="grid grid-cols-1 content-center text-center w-full h-full">
          <div class="flex items-center p-4 mb-4 text-m text-red-800 rounded bg-red-50" role="alert">
            <svg class="flex-shrink-0 inline w-4 h-4 me-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z" />
            </svg>
            <span class="sr-only">Info</span>
            <div>
              <span class="font-medium">Error!</span> {errorMsg}
            </div>
          </div>
        </div>
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
                    debug: true,
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
