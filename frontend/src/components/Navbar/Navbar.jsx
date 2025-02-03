import { Link, NavLink } from "react-router-dom";
import { useState } from "react";

import AddCameraModal from "../Cameras/AddCameraModal";
import DropdownMenu from "../DropdownMenu/DropdownMenu";
import Caret from "../DropdownMenu/Caret";

const Navbar = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showModal, setShowModal] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-black p-4">
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
            <Link to="/cameras" onClick={() => setDropdownOpen(false)} className="text-white hover:text-gold">Cameras</Link>
            <Caret setDropdownOpen={setDropdownOpen} />
          </div>
          <DropdownMenu
            items={[
              { value: "Add Camera", onClick: () => setShowModal(true) },
            ]}
            open={dropdownOpen}
            setOpen={setDropdownOpen} />
        </li>
      </ul>
      <AddCameraModal showModal={showModal} setShowModal={setShowModal} />
    </nav>
  );
};

export default Navbar;