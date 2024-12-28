import Home from "./components/Home";
import Cameras from "./components/Cameras/Cameras"

import { Route, Routes, NavLink, HashRouter } from "react-router-dom";

const App = () => {
  return (
    <HashRouter>
      <div className="App">
        <ul className="header">
          <li><NavLink to="/">Home</NavLink></li>
          <li><NavLink to="/cameras">Cameras</NavLink></li>
        </ul>
        <div className="content">
          <Routes>
            <Route exact path="/" element={<Home />}></Route>
            <Route exact path="/cameras" element={<Cameras />}></Route>
          </Routes>
        </div>
      </div>
    </HashRouter>
  );
}

export default App;
