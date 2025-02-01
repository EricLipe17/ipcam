import Home from "./components/Home";
import Cameras from "./components/Cameras/Cameras"
import Navbar from "./components/Navbar/Navbar"
import WSCamera from "./components/Camera/WSCamera";

import { Route, Routes, BrowserRouter } from "react-router-dom";

const App = () => {
  return (
    <BrowserRouter>
      <div className="App">
        <Navbar />
        <div className="content">
          <Routes>
            <Route exact path="/" element={<Home />} />
            <Route exact path="/cameras" element={<Cameras />} />
            <Route exact path="/ws" element={<WSCamera />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
