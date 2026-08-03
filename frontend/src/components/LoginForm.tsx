import { useContext, useState } from "react";
import { AuthContext } from "../services/AuthContext";
import SubmitLoginForm from "../services/SubmitLoginForm";

function LoginForm() {
    const { setToken } = useContext(AuthContext);
    const [ isValidUser, setIsValidUser ] = useState(true);
    
    const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        const username = (e.currentTarget.getElementsByClassName("form-control")[0] as HTMLInputElement).value;
        const password = (e.currentTarget.getElementsByClassName("form-control")[1] as HTMLInputElement).value;
        const result = await SubmitLoginForm(username, password);
        if (result.success) {
            // Store the token in context for future requests
            localStorage.setItem("token", result.data.access_token);
            setToken(result.data.access_token);
            setIsValidUser(true);
        } else {
            setIsValidUser(false);
        }
    }
    
    return (
        <>
            <form onSubmit={handleSubmit}>
                {!isValidUser && (
                    <div className="text-danger">
                        Invalid username or password
                    </div>
                )}
                <div className="mb-3">
                    <label className="form-label">Username</label>
                    <input type="text" className="form-control" id="exampleInputEmail1" aria-describedby="emailHelp" />
                </div>
                <div className="mb-3">
                    <label className="form-label">Password</label>
                    <input type="password" className="form-control" id="exampleInputPassword1" />
                </div>
                
                <div className="mb-3 form-check">
                    <input type="checkbox" className="form-check-input" id="exampleCheck1" />
                    <label className="form-check-label" >Check me out</label>
                </div>
                <button type="submit" className="btn btn-primary">Submit</button>
            </form>
        </>
    )
}

export default LoginForm;
