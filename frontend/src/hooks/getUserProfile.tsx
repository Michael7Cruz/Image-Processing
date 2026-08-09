import { useContext, useEffect, useState } from "react";
import { AuthContext } from "../services/AuthContext";
import { refreshAccessToken } from "../services/RefreshToken";

async function viewUser(token: string | null) {
    const res = await fetch("http://localhost:8000/users/me", 
                {
                    method:"GET",
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

    return res;
}

// Get user profile data from the backend using the token stored in localStorage or context
export default function getUserProfile() {
    const { token, setToken } = useContext(AuthContext);
    const [user, setUser] = useState({"username": "...", "email": "...", "full_name": "...", "disabled": true});

    useEffect(() => {
        let currentToken = token;

        if (!currentToken) return;

        async function fetchUser() {
            let res = await viewUser(currentToken);

            // If the access token is expired, try to refresh it
            if (res.status === 401) {
                const newToken = await refreshAccessToken();
                console.log("Access token refreshed:");
                if (!newToken) {
                    // Refresh token is also invalid/expired
                    localStorage.removeItem("token");
                    setToken(null);
                    return;
                }

                currentToken = newToken;

                // Tell React about the new token
                setToken(newToken);

                // Retry request
                res = await viewUser(currentToken);
            }

            if (res.ok) {
                const userData = await res.json();
                setUser(userData);
            }
        }

        fetchUser();
    }, [token]); // runs when the token changes

    return user;
}