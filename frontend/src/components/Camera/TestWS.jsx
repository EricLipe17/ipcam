import React, { memo, useEffect, useRef, useState } from "react"
import Error from "../Errors/Error"

const TestWS = memo(({ config }) => {
  const videoRef = useRef(null)
  const wsRef = useRef(null)

  // const CODECS = [
  //   "avc1.640029", // H.264 high 4.1 (Chromecast 1st and 2nd Gen)
  //   "avc1.64002A", // H.264 high 4.2 (Chromecast 3rd Gen)
  //   "avc1.640033", // H.264 high 5.1 (Chromecast with Google TV)
  //   "hvc1.1.6.L153.B0", // H.265 main 5.1 (Chromecast Ultra)
  //   "mp4a.40.2", // AAC LC
  //   "mp4a.40.5", // AAC HE
  // ]

  const [errorMsg, setErrorMsg] = useState("")

  useEffect(() => {
    wsRef.current = new WebSocket(`ws://localhost:8000/cameras/${config.id}/live`)
    wsRef.current.onmessage = (event) => {
      // For the moment, we're assuming that the server is sending us binary mp4 segments only
      event.data.arrayBuffer().then((segment) => {
        console.log('Got segment for cam', config.id)
      })
    }

    wsRef.current.onopen = (event) => {
      console.log('Websocket connection opened for cam:', config.id)
    }

    wsRef.current.onerror = (event) => {
      console.log('Websocket error for cam', config.id)
      console.log('error:', event)
    }

    wsRef.current.onclose = (event) => {
      console.log('Websocket closing for cam', config.id)
    }


    return () => {
      wsRef.current.close()
    }
  }, [])


  return (
    <div className="w-fit h-fit">
      {errorMsg !== "" ? (
        <Error errorMsg={errorMsg} />
      ) :
        (
          <>
            <div className="flex space-x-5 bg-black border border-white">
              <span>ID: {config.id}</span>
              <span>Name: {config.name}</span>
              {config.location && <span>Location: {config.location}</span>}
            </div>
            <video ref={videoRef} controls autoPlay={true} muted={true} width={426} height={240} />
          </>
        )
      }
    </div >
  )
})

export default TestWS
