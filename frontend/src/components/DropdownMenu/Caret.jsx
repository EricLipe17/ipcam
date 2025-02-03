import { FaCaretDown } from "react-icons/fa";
import React, { useEffect, useRef } from "react";


const Caret = ({ setDropdownOpen }) => {
  const ref = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [ref, setDropdownOpen]);

  return (
    <button
      ref={ref}
      onClick={() => setDropdownOpen((prev) => !prev)}
      className="text-white hover:text-gold"
    >
      <FaCaretDown className="ml-1" />
    </button>
  )
};

export default Caret;