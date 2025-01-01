import { NavLink } from "react-router-dom";

const Navbar = () => {
  return (
    <nav className="navbar">
      <ul className="header">
        <li><NavLink to="/">Home</NavLink></li>
        <li><NavLink to="/cameras">Cameras</NavLink></li>
      </ul>
    </nav>
  );
};

export default Navbar;
