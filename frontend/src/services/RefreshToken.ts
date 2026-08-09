export async function refreshAccessToken(): Promise<string | null> {
    const response = await fetch("http://127.0.0.1:8000/users/refresh", {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        return null;
    }

    const data = await response.json();

    const newToken = data.access_token;

    localStorage.setItem("token", newToken);

    return newToken;
}