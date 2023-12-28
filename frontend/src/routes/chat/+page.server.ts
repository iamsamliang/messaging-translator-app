import { redirect } from '@sveltejs/kit';

export async function load({ cookies }) {
    const token: string | undefined = cookies.get("jwt");

    if (token === undefined) throw redirect(302, "/login");
    
    // grab the current user from backend using the cookie
    const response: Response = await fetch("http://localhost:8000/users/me", {
        method: "GET",
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) throw redirect(302, "/login");
    
    const user = await response.json();

    return {
        user
    };
}