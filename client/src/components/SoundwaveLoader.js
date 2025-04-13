import React from 'react';
import '../components/styling/soundwave.css';
import vinylVideo from '../assets/background_video/vinylVideo.mp4';

const SoundwaveLoader = ({ message = "Getting your tracks ready..." }) => {
    return (
            <div className="soundwave-loader">
            <video 
                autoPlay 
                loop 
                muted 
                playsInline 
                className="vinyl-background"
            >
                <source src={vinylVideo} type="video/mp4" />
                Your browser does not support the video tag.
            </video>
            <div className="soundwave-loader-container">
                <h1 className="soundwave-loader-title">Loading Your Music</h1>
                <p className="soundwave-loader-subtitle">{message}</p>
                <div className="soundwave-bars-container">
                    {[...Array(12)].map((_, index) => (
                    <div 
                        key={index}
                        className="soundwave-bar"
                        style={{ animationDelay: `${index * 0.1}s` }}
                    />
                    ))}
            </div>
            </div>
            </div>
        );
    };

export default SoundwaveLoader;