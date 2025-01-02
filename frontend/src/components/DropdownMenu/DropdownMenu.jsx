import React, { useEffect, useRef } from "react";


const DropdownMenu = ({ items, open, setOpen }) => {
  const ref = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [ref]);

  return (
    <>
      {open && (
        <div ref={ref} class="z-10 rounded-lg border border-gold bg-black">
          <ul class="py-2 text-sm">
            {items.map((item, index) => (
              <li key={index} onClick={item.onClick} className="hover:text-gold ml-2 mr-2">
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