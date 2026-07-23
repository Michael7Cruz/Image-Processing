import LoginForm from "./components/LoginForm"
import { useState } from "react"

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  return <>
    {isLoggedIn ? (
        <div>Success</div>
      ):(
        <div className="row justify-content-center">
          <div className="col-4 p-5 mt-5 border rounded-3 shadow">
            <LoginForm onLogInSuccess={() => setIsLoggedIn(true)}/>
          </div>
        </div>
      )
    }
    
  </>
}
export default App
