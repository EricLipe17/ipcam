const Grid = ({ children }) => {
  return (
    <div
      className={`grid gap-5 h-fit w-fit auto-cols-max`}
    >
      {children}
    </div>
  );
};

export default Grid;