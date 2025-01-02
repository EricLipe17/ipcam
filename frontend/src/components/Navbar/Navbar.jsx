import { Link, NavLink } from "react-router-dom";
import { useState } from "react";
import { FaCaretDown } from "react-icons/fa";

import AddCameraModal from "../Cameras/AddCameraModal";
import DropdownMenu from "../DropdownMenu/DropdownMenu";

const Navbar = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const handleModal = (show) => {
    setShowModal(show)
    setDropdownOpen(false)
  }

  return (
    <nav className="bg-black p-4">
      <ul className="flex space-x-4">
        <li>
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive
                ? "text-gold font-bold"
                : "text-white hover:text-gold"
            }
          >
            Home
          </NavLink>
        </li>
        <li className="relative">
          <div className="grid grid-cols-2">
            <Link to="/cameras" onClick={() => setDropdownOpen(false)} className="text-white hover:text-gold flex items-center">Cameras</Link>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="text-white hover:text-gold flex items-center"
            >
              <FaCaretDown className="ml-1" />
            </button>
          </div>

          {true && (
            <DropdownMenu
              items={[
                { value: "Add Camera", onClick: () => handleModal(true) },
              ]}
              open={dropdownOpen}
              setOpen={setDropdownOpen} />
          )}
        </li>
      </ul>
      <AddCameraModal showModal={showModal} handleModal={handleModal} />
    </nav>
  );
};

export default Navbar;