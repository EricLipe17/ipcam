import { FaCaretDown, FaCaretUp } from "react-icons/fa";

const Caret = ({ dropdownOpen, setDropdownOpen }) => {
  return (
    <>
      {
        !dropdownOpen ? (
          <button
            onClick={() => setDropdownOpen(true)}
            className="text-white hover:text-gold"
          >
            <FaCaretDown className="ml-1" />
          </button>
        ) : (
          <button
            onClick={() => setDropdownOpen(false)}
            className="text-white hover:text-gold"
          >
            <FaCaretUp className="ml-1" />
          </button>
        )
      }
    </>
  )
};

export default Caret;