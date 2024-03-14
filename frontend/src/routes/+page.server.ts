export async function load({ cookies }) {
    const token: string | undefined = cookies.get("jwt");

    if (token === undefined) return;
    
    // grab the current user from backend using the cookie
    const response: Response = await fetch("http://localhost:8000/users/me/default", {
        method: "GET",
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) return;

    const user = await response.json();

    return {
        user
    };
}