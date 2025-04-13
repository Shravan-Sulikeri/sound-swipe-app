import React from 'react';
import '../components/styling/nosongs.css';
import exitVideo from '../assets/background_video/exit.mp4';

const NoSongsScreen = ({ onRefresh }) => {
    //! Need to fix the refresh button, doesn't actually work just there for show
    return (
            <div className="no-songs-screen">
            <video 
                autoPlay 
                loop 
                muted 
                playsInline 
                className="vinyl-background"
            >
                <source src={exitVideo} type="video/mp4" />
            </video>
            
            <div className="no-songs-content">
                <h1>No more songs 😔</h1>
                <p>You’ve reached the end or something went offbeat. Try refreshing!</p>
                
                <div className="record-scratch-effect">
                <div className="scratch-line"></div>
                <div className="scratch-line"></div>
                <div className="scratch-line"></div>
                </div>
                
                <button className="refresh-button" onClick={onRefresh}>
                Keep the Vibes Going
                </button>
            </div>
            </div>
        );
    };

export default NoSongsScreen;