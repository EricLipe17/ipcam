import { useEffect, useState } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  rectSortingStrategy
} from "@dnd-kit/sortable";

import Camera from '../Camera/Camera';
import Grid from '../Grid/Grid';
import SortableItem from '../SortableItem/SortableItem';

const Cameras = () => {
  const [activeId, setActiveId] = useState(null);
  const [cameras, setCameras] = useState([])
  const [width, setWidth] = useState(window.innerWidth);

  const cols = Math.floor(width / 640)

  const fetchCameras = () => {
    fetch("http://localhost:8000/cameras/").then(response => response.json())
      .then(cameras => setCameras(cameras))
      .catch(error => console.error('Error:', error));
  }

  const handleResize = () => setWidth(window.innerWidth);

  const sensors = useSensors(
    useSensor(PointerSensor),
  );

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = (event) => {
    setActiveId(null);
    const { active, over } = event;

    if (active.id !== over.id) {
      setCameras((cameras) => {
        const oldCameraConfig = cameras.find(conf => conf.id === active.id);
        const overCamerConfig = cameras.find(conf => conf.id === over.id);
        const oldIndex = cameras.indexOf(oldCameraConfig)
        const newIndex = cameras.indexOf(overCamerConfig);

        return arrayMove(cameras, oldIndex, newIndex);
      });
    }
  };

  useEffect(() => {
    window.addEventListener("resize", handleResize);
    fetchCameras() // TODO: This is inneficient because the Camera component has to duplicate the request to ensure pureness and make sure the livestream for itself has officially been published.
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="bg-black-950 min-h-screen p-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
        onDragStart={handleDragStart}
      >
        <SortableContext items={cameras} strategy={rectSortingStrategy}>
          <Grid columns={cols}>
            {cameras.map((camera) => (
              <SortableItem key={camera.id} id={camera.id} handle={true}>
                <Camera id={camera.id} />
              </SortableItem>
            ))}
          </Grid>
        </SortableContext>
        <DragOverlay>
          {activeId ? (
            <div
              className="w-640 h-360 bg-gold opacity-30 z-auto"
            ></div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}

export default Cameras;
