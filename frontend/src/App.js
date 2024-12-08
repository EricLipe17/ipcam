import Home from "./components/Home";
import About from "./components/About";
import Contact from "./components/Contact";
import Cameras from "./components/Cameras"

import React, { Component } from "react";
import { Route, Routes, NavLink, HashRouter } from "react-router-dom";

class App extends Component {
  render() {
    return (
      <HashRouter>
        <div className="App">
          <ul className="header">
            <li><NavLink to="/">Home</NavLink></li>
            <li><NavLink to="/about">About</NavLink></li>
            <li><NavLink to="/contact">Contact</NavLink></li>
            <li><NavLink to="/cameras">Cameras</NavLink></li>
          </ul>
          <div className="content">
            <Routes>
              <Route exact path="/" element={<Home />}></Route>
              <Route exact path="/about" element={<About />}></Route>
              <Route exact path="/contact" element={<Contact />}></Route>
              <Route exact path="/cameras" element={<Cameras />}></Route>
            </Routes>
          </div>
        </div>
      </HashRouter>
    );
  }
  }
  export default App;
