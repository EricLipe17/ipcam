const Grid = ({ children, columns }) => {
  return (
    <div
      className={`grid gap-5`}
      style={{
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
      }}
    >
      {children}
    </div>
  );
};

export default Grid;