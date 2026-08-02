import { AuthContext } from "../services/AuthContext";
import { useContext, useEffect, useState } from "react";

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

function UserProfile() {
    const [user, setUser] = useState({"username": "...", "email": "...", "full_name": "...", "disabled": true});
    const storedToken = localStorage.getItem("token");
    const { token } = useContext(AuthContext);
    const { setToken } = useContext(AuthContext);
    const handleLogout = () => {
        localStorage.removeItem("token");
        setToken(null);
    };

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

    return ( 
        <>
            <div className="container d-flex justify-content-center mt-5">
                <div className="card p-4 shadow-sm" style={{ maxWidth: "400px", width: "100%" }}>
                    <h3 className="mb-3">{user.full_name}</h3>

                    <p className="mb-1">
                        <strong>Username:</strong> {user.username}
                    </p>

                    <p className="mb-1">
                        <strong>Email:</strong> {user.email}
                    </p>

                    <span className={`badge ${user.disabled ? "bg-secondary" : "bg-success"} mt-2`}>
                        {user.disabled ? "Disabled" : "Active"}
                    </span>

                    <button className="btn btn-outline-danger w-100 mt-4" onClick={handleLogout}>
                        Log Out
                    </button>
                </div>
            </div>
        </>
    );
}

export default UserProfile;