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

    const user = await response.json();

    return {
        user
    };
}

export const actions = {
    logout: ({ cookies }) => {
        cookies.delete("jwt", { path: "/" });

        // to prevent the browser asking to resubmit the form when refreshing page
        throw redirect(303, '/');
    }
};