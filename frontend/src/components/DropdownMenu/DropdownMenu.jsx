const DropdownMenu = ({ items, open, setOpen }) => {

  return (
    <>
      {open && (
        <div className="z-10 rounded-lg border border-gold bg-black">
          <ul className="py-2 text-sm">
            {items.map((item, index) => (
              <li key={index} onClick={() => {
                item.onClick()
                setOpen(false)
              }} className="hover:text-gold ml-2 mr-2">
                {item.value}
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
};


export default DropdownMenu;