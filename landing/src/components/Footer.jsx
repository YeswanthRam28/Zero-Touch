import React from 'react';

const Footer = () => {
  return (
    <footer className="py-8 mt-12 border-t border-t-[#1a1a1a]">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="text-sm text-gray-400">© {new Date().getFullYear()} Zero-Touch Surgical • Research & Demo</div>
        <div className="flex items-center gap-4">
          <a className="text-sm text-gray-300 hover:text-white" href="#">Docs</a>
          <a className="text-sm text-gray-300 hover:text-white" href="#">Research</a>
          <a className="text-sm text-gray-300 hover:text-white" href="#">Contact</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
