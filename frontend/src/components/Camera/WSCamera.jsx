import React, { memo, useEffect, useRef, useState } from "react"
import Error from "../Errors/Error"

const WSCamera = memo(({ config }) => {
  console.log('rendering WSCamera')
  const videoRef = useRef(null)
  const mediaSrcRef = useRef(new MediaSource())
  const bufferRef = useRef(null)
  const wsRef = useRef(new WebSocket(`ws://localhost:8000/cameras/${config.id}/live`))

  // const CODECS = [
  //   "avc1.640029", // H.264 high 4.1 (Chromecast 1st and 2nd Gen)
  //   "avc1.64002A", // H.264 high 4.2 (Chromecast 3rd Gen)
  //   "avc1.640033", // H.264 high 5.1 (Chromecast with Google TV)
  //   "hvc1.1.6.L153.B0", // H.265 main 5.1 (Chromecast Ultra)
  //   "mp4a.40.2", // AAC LC
  //   "mp4a.40.5", // AAC HE
  // ]

  const [errorMsg, setErrorMsg] = useState("")

  // TODO: something here is not letting concurrent ws connections occur.

  useEffect(() => {
    console.log('Creating MediaSource for', config.id)
    const video = videoRef.current
    const mediaSrc = mediaSrcRef.current
    const websocket = wsRef.current
    let mimeCodec = 'video/mp4; codecs="avc1.640033,mp4a.40.5"'

    websocket.onmessage = (event) => {
      console.log('received message for', config.id)
      // For the moment, we're assuming that the server is sending us binary mp4 segments only
      event.data.arrayBuffer().then((segment) => {
        console.log('converted to arraybuffer for', config.id)
        bufferRef.current.appendBuffer(segment)
      })
    }

    websocket.onopen = (event) => {
      console.log('Websocket connection opened for cam:', config.id)
      websocket.send('next')
    }

    websocket.onerror = (event) => {
      console.log('Websocket error for cam', config.id)
      console.log('error:', event)
    }

    websocket.onclose = (event) => {
      console.log('Websocket closing for cam', config.id)
    }

    video.src = URL.createObjectURL(mediaSrc)
    video.ontimeupdate = (event) => {
      console.log('Current time', video.currentTime)
      websocket.send('next')
    }

    mediaSrc.addEventListener('error', (event) => {
      setErrorMsg('MediaSource error:', event)
      console.error('MediaSource error:', event)
    })

    mediaSrc.addEventListener('sourceopen', () => {
      // console.log('MediaSource opened')
      if (!MediaSource.isTypeSupported(mimeCodec)) {
        setErrorMsg('Unsupported MIME type or codec: ', mimeCodec)
        return
      }
      bufferRef.current = mediaSrc.addSourceBuffer(mimeCodec)
      bufferRef.current.mode = 'sequence'

      bufferRef.current.addEventListener('error', (event) => { setErrorMsg('SourceBuffer error:', event) })
      bufferRef.current.addEventListener('updateend', () => {
        console.log('Getting next segment for cam', config.id)
        websocket.send('next')
      })
    })

    return () => {
      websocket.close()
      mediaSrc.endOfStream()
      console.log('MediaSource closed')
    }
  }, [])


  return (
    <div className="w-fit h-fit">
      {errorMsg !== "" ? (
        <Error errorMsg={errorMsg} />
      ) :
        (
          <>
            <div className={`flex space-x-5 bg-black border border-white`}>
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
