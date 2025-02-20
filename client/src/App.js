import React, {useState, useEffect} from"react";
import Login from "./Login";
import axios from "axios";


function App() {
  const [accessToken, setAccessToken] = useState(null);

  useEffect(() => {
    //Get the access token from URL hash after login
    const hash = window.location.hash;
    if (hash) {
      const token = new URLSearchParams(hash.substring(1)).get("access_token");
      if (token) {
        setAccessToken(token);
        localStorage.setItem("spotify_access_token", token);
        window.location.hash = ""; // Clear the URL after storing token
      }
    }
  }, []);

  return (
    <div>
      {accessToken ? ( 
        <h1>Logged in! Now you can explore music.</h1>


      ): (
        <Login />
      )}
    </div>
  );
}
export default App;