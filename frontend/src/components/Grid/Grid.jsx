const Grid = ({ children, columns }) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gridGap: 10,
        margin: '100px auto',
      }}
    >
      {children}
    </div>
  );
};

export default Grid;
