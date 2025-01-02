import React from "react";

const Home = () => {
  return (
    <div className="bg-black-950 min-h-screen flex flex-col items-center justify-center text-white">
      <h1 className="text-5xl font-bold text-gold mb-4">V.I.P.E.R - Home</h1>
      <p className="text-lg text-gray-300 mb-8">
        This is a paragraph on the HomePage of the SPA App.
      </p>
      <button className="bg-gold text-black py-2 px-4 rounded hover:bg-white hover:text-black transition duration-300">
        Learn More
      </button>
    </div>
  );
};

export default Home;