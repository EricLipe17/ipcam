import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
const SortableItem = ({ id, children }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: id });

  const dynamicStyle = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? "100" : "auto",
    opacity: isDragging ? 0.3 : 1
  };

  return (
    <div ref={setNodeRef} style={dynamicStyle} className="min-h-[360px] min-w-[640px] h-fit w-fit border-2 border-gold bg-black m-2 rounded" {...attributes} {...listeners}>
      {children}
    </div >
  );
};

export default SortableItem;
