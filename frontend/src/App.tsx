import LoginForm from "./components/LoginForm"
import { useEffect, useState } from "react"
import { AuthContext } from "./services/AuthContext";
import UserProfile from "./components/UserProfile";

function App() {
  const [token, setToken] = useState<string | null>(null);
  // If there's no token in state but there's one in localStorage, set it in state
  useEffect(() => {
    const storedToken = localStorage.getItem("token");

    if (storedToken) {
        setToken(storedToken);
    }
  }, []);
  
  return <>
    <AuthContext.Provider value={{ token, setToken }}>
    {token ? (
        <UserProfile />
      ):(
        <div className="row justify-content-center">
          <div className="col-6 p-5 mt-5 border rounded-3 shadow">
            
              <LoginForm />
            
          </div>
        </div>
      )
    }
    </AuthContext.Provider>
    
  </>
}
export default App
