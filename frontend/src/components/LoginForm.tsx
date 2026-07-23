import SubmitLoginForm from "../services/SubmitLoginForm";

interface LogInFormProps {
    onLogInSuccess: () => void;
}

function LoginForm({onLogInSuccess}: LogInFormProps) {
    const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        const result = await SubmitLoginForm(
            (e.currentTarget.getElementsByClassName("form-control")[0] as HTMLInputElement).value,
            (e.currentTarget.getElementsByClassName("form-control")[1] as HTMLInputElement).value
        );  
        if (result.success) {
            onLogInSuccess();
            /*sample fetch while authorized*/
            const res = await fetch("http://localhost:8000/image/viewall", 
                {
                    method:"GET",
                    headers: {
                        Authorization: `Bearer ${result.data.access_token}`
                    }

                }
            )
            console.log(await res.json())
        }
    }
    
    return (
        <>
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label className="form-label">Username</label>
                    <input type="text" className="form-control" id="exampleInputEmail1" aria-describedby="emailHelp" />
                    <div id="emailHelp" className="form-text">We'll never share your username with anyone else.</div>
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
