import { Link, NavLink } from "react-router-dom";
import { useState } from "react";
import { FaCaretDown } from "react-icons/fa";

import AddCameraModal from "../Cameras/AddCameraModal";

const Navbar = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

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

          {dropdownOpen && (
            <ul className="absolute left-0 mt-2 w-48 bg-black border border-gray-700 rounded shadow-lg">
              <li>
                <AddCameraModal />
              </li>
            </ul>
          )}
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;