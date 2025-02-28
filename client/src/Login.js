import React, { useEffect, useRef } from "react";
import './App.css';

const Login = () => {
  const interBubbleRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const interBubble = interBubbleRef.current;
    const container = containerRef.current;
    if (!interBubble || !container) return;

    let curX = 0;
    let curY = 0;
    let tgX = 0;
    let tgY = 0;

    function move() {
      curX += (tgX - curX) / 20;
      curY += (tgY - curY) / 20;
      if (interBubble) {
        interBubble.style.transform = `translate(${Math.round(curX)}px, ${Math.round(curY)}px)`;
      }
      requestAnimationFrame(move);
    }

    function handleMouseMove(event) {
      const rect = container.getBoundingClientRect();
      tgX = event.clientX - rect.left;
      tgY = event.clientY - rect.top;
    }

    container.addEventListener('mousemove', handleMouseMove);
    move();

    return () => {
      container.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const handleLogin = () => {
    window.location.href = "http://localhost:3001/login";
  };

  return (
    <div className="App">
      <div ref={containerRef} className="gradient-bg">
        <svg xmlns="http://www.w3.org/2000/svg">
          <defs>
            <filter id="goo">
              <feGaussianBlur in="SourceGraphic" stdDeviation="40" result="blur" />
              <feColorMatrix
                in="blur"
                mode="matrix"
                values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 35 -7"
                result="goo"
              />
              <feBlend in="SourceGraphic" in2="goo" />
            </filter>
          </defs>
        </svg>
        <div className="gradients-container">
          <div className="g1"></div>
          <div className="g2"></div>
          <div className="g3"></div>
          <div className="g4"></div>
          <div className="g5"></div>
          <div className="interactive" ref={interBubbleRef}></div>
        </div>
        <div className="text-container" style={{ pointerEvents: 'none' }}>
          <div className="login-content" style={{ pointerEvents: 'auto' }}>
            <h1>
              Welcome to 
              <img 
                alt="logo" 
                className="logo" 
                src={require('./assets/soundswipe-logo-zip-file/png/logo-no-background.png')}
                style={{ marginLeft: '10px', verticalAlign: 'middle' }}
              />
            </h1>
            <p className="subtitle">Discover new music tailored to your taste</p>
            <button onClick={handleLogin} className="login-button">
              Login with Spotify
            </button>
            <p className="powered-by">
              Powered by
              <img alt="Spotify" src={require('./assets/Spotify_logo_with_text.svg.png')} />
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;