import React, { useEffect, useRef, useState } from "react"

const WSCamera = ({ streamUrl }) => {
  const videoRef = useRef(null)
  const mediaSourceRef = useRef(null)
  const bufferRef = useRef(null)

  const CODECS = [
    "avc1.640029", // H.264 high 4.1 (Chromecast 1st and 2nd Gen)
    "avc1.64002A", // H.264 high 4.2 (Chromecast 3rd Gen)
    "avc1.640033", // H.264 high 5.1 (Chromecast with Google TV)
    "hvc1.1.6.L153.B0", // H.265 main 5.1 (Chromecast Ultra)
    "mp4a.40.2", // AAC LC
    "mp4a.40.5", // AAC HE
  ]

  useEffect(() => {
    const video = videoRef.current
    mediaSourceRef.current = new MediaSource()
    let mimeCodec = 'video/mp4; codecs="avc1.640033,mp4a.40.2"'

    const ws = new WebSocket('ws://localhost:8000/cameras/1/live')

    video.src = URL.createObjectURL(mediaSourceRef.current)

    mediaSourceRef.current.addEventListener('error', (event) => {
      console.error('MediaSource error:', event)
    })

    mediaSourceRef.current.addEventListener('sourceopen', () => {
      console.log('MediaSource opened')
      if (!MediaSource.isTypeSupported(mimeCodec)) {
        console.error('Unsupported MIME type or codec: ', mimeCodec)
        return
      }
      bufferRef.current = mediaSourceRef.current.addSourceBuffer(mimeCodec)

      bufferRef.current.addEventListener('error', (event) => { console.error('SourceBuffer error:', event) })

      ws.onmessage = (event) => {
        console.log('Received data', event.data)
        event.data.arrayBuffer().then((segment) => {
          console.log('Appending segment to buffer', segment)
          if (bufferRef.current.updating) {
            console.log('Buffer is updating, waiting for updateend event to append segment')
          } else {
            console.log('Buffer is not updating, appending segment')
            bufferRef.current.appendBuffer(segment)
          }
        })
      }
    })

    return () => ws.close()
  })


  return (
    <video ref={videoRef} controls autoPlay={true} muted={true} />
  )
}

export default WSCamera
