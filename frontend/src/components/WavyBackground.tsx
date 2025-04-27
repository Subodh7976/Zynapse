import React from 'react';

const WavyBackground = () => {
  return (
    <div className="absolute bottom-0 left-0 w-full h-60 sm:h-72 md:h-80 lg:h-96 pointer-events-none overflow-hidden z-0">
      <div className="absolute bottom-0 left-0 w-[200%] h-full animate-wave-slide">
        {/* Wave 1 (Darker Purple, slightly slower bob) */}
        <svg
          className="absolute bottom-0 w-full h-full text-purple-700 opacity-80 animate-wave-bob [animation-duration:6s]" // Slower bob
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 1440 320"
          preserveAspectRatio="none"
        >
          <path
            fill="currentColor"
            fillOpacity="1"
            d="M0,192L48,176C96,160,192,128,288,133.3C384,139,480,181,576,186.7C672,192,768,160,864,144C960,128,1056,128,1152,149.3C1248,171,1344,213,1392,234.7L1440,256L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          ></path>
        </svg>

        {/* Wave 2 (Lighter Purple, slightly faster bob) */}
        <svg
          className="absolute bottom-0 w-full h-full text-purple-500 opacity-70 animate-wave-bob [animation-duration:5s]" // Default bob speed
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 1440 320"
          preserveAspectRatio="none"
          style={{ transform: 'translateX(10%) translateY(10px)' }}
        >
          <path
            fill="currentColor"
            fillOpacity="1"
            // Slightly different wave path
            d="M0,224L60,213.3C120,203,240,181,360,186.7C480,192,600,224,720,240C840,256,960,256,1080,234.7C1200,213,1320,171,1380,149.3L1440,128L1440,320L1380,320C1320,320,1200,320,1080,320C960,320,840,320,720,320C600,320,480,320,360,320C240,320,120,320,60,320L0,320Z"
          ></path>
        </svg>
      </div>
    </div>
  );
};

export default WavyBackground;