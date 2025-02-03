import React, { memo, useEffect, useRef, useState } from "react"
import Error from "../Errors/Error"

const WSCamera = memo(({ config }) => {
  console.log('rendering WSCamera')
  const videoRef = useRef(null)
  const mediaSourceRef = useRef(null)
  const bufferRef = useRef(null)
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
    const video = videoRef.current
    mediaSourceRef.current = new MediaSource()
    let mimeCodec = 'video/mp4; codecs="avc1.640033,mp4a.40.5"'

    wsRef.current = new WebSocket('ws://localhost:8000/cameras/1/live')
    wsRef.current.onmessage = (event) => {
      // For the moment, we're assuming that the server is sending us binary mp4 segments only
      event.data.arrayBuffer().then((segment) => {
        console.log('Appending segment')
        bufferRef.current.appendBuffer(segment)
      })
    }

    video.src = URL.createObjectURL(mediaSourceRef.current)

    mediaSourceRef.current.addEventListener('error', (event) => {
      setErrorMsg('MediaSource error')
      console.error('MediaSource error:', event)
    })

    mediaSourceRef.current.addEventListener('sourceopen', () => {
      console.log('MediaSource opened')
      if (!MediaSource.isTypeSupported(mimeCodec)) {
        setErrorMsg('Unsupported MIME type or codec: ', mimeCodec)
        return
      }
      bufferRef.current = mediaSourceRef.current.addSourceBuffer(mimeCodec)
      bufferRef.current.mode = 'sequence'

      bufferRef.current.addEventListener('error', (event) => { setErrorMsg('SourceBuffer error:', event) })
      bufferRef.current.addEventListener('updateend', () => {
        wsRef.current.send('next')
      })
    })

    return () => {
      wsRef.current.close()
    }
  })


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

export default WSCamera
