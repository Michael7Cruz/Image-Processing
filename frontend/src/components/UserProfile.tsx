import getUserProfile from "../hooks/getUserProfile";
import { AuthContext } from "../services/AuthContext";
import { useContext } from "react";



function UserProfile() {
    const user = getUserProfile();
    const { setToken } = useContext(AuthContext);
    const handleLogout = () => {
        localStorage.removeItem("token");
        setToken(null);
    };
    
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