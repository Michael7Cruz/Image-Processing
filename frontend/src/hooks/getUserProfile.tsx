import { useContext, useEffect, useState } from "react";
import { AuthContext } from "../services/AuthContext";

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
    const storedToken = localStorage.getItem("token");
    const { token } = useContext(AuthContext);
    const [user, setUser] = useState({"username": "...", "email": "...", "full_name": "...", "disabled": true});

    useEffect(() => {
        const currentToken = token || storedToken;

        if (!currentToken) return;

        async function fetchUser() {
            const res = await viewUser(currentToken);

            if (res.ok) {
                const userData = await res.json();
                setUser(userData);
            }
        }

        fetchUser();
    }, [token]); // runs when the token changes

    return user;
}