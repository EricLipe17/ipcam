import React, { useEffect, useState, useRef } from "react";

const Grid = ({ children }) => {
  const [numColumns, setNumColumns] = useState(1);
  const ref = useRef(null);

  useEffect(() => {
    const calculateColumns = () => {
      if (ref.current) {
        const containerWidth = ref.current.offsetWidth;
        const childWidth = ref.current.firstChild ? ref.current.firstChild.offsetWidth : 0;
        const columns = childWidth ? Math.floor(containerWidth / childWidth) : 1;
        setNumColumns(columns);
      }
    };

    calculateColumns();
    window.addEventListener("resize", calculateColumns);

    return () => {
      window.removeEventListener("resize", calculateColumns);
    };
  }, [children]);

  return (
    <div
      ref={ref}
      className={`grid gap-5 h-fit w-full`}
      style={{
        gridTemplateColumns: `repeat(${numColumns}, minmax(0, 1fr))`,
      }}
    >
      {children}
    </div>
  );
};

export default Grid;