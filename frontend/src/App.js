import Home from "./components/Home";
import Cameras from "./components/Cameras/Cameras"
import Navbar from "./components/Navbar/Navbar";

import { Route, Routes, HashRouter } from "react-router-dom";

const App = () => {
  return (
    <HashRouter>
      <div className="App">
        <Navbar />
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
