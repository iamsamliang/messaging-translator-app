import serverSettings from '$lib/config/config.server.js';
import { redirect } from '@sveltejs/kit';

export async function load({ cookies }) {
    const token: string | undefined = cookies.get("jwt");

    if (!token) return;
    
    // grab the current user from backend using the cookie
    const response: Response = await fetch(`${serverSettings.apiBaseURL}/users/me/default`, {
        method: "GET",
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) return;
    
    throw redirect(303, "/chat")
}