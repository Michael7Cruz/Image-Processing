export default async function submitLoginForm(username: string, password: string) {
    try {
        const response = await fetch("http://localhost:8000/users/token", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
                username,
                password,
            }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Login successful");
        return {success: true, data};
    } catch (error) {
        console.error("Login failed:", error);
        return {success: false};
    }
}
