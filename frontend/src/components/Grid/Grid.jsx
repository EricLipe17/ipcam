const Grid = ({ children, columns }) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gridGap: 10,
      }}
    >
      {children}
    </div>
  );
};

export default Grid;
