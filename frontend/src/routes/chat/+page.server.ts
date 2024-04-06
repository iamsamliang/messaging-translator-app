import { redirect } from '@sveltejs/kit';
import serverSettings from '$lib/config/config.server.js';

export async function load({ cookies }) {
    const token: string | undefined = cookies.get("jwt");

    if (token === undefined) redirect(303, "/login");
    
    // grab the current user from backend using the cookie
    const response: Response = await fetch(`${serverSettings.apiBaseURL}/users/me/extra-info`, {
        method: "GET",
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) redirect(303, "/login");
    
    const user = await response.json();

    return {
        user
    };
}