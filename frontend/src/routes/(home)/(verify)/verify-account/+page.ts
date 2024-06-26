import clientSettings from '$lib/config/config.client.js';
import { error } from '@sveltejs/kit';

export async function load({ url, fetch }) {
    const token = url.searchParams.get("token");

    if (!token) {
		error(404, {
        			message: 'Invalid Permissions.'
        		});
    }

    const response: Response = await fetch(`${clientSettings.apiBaseURL}/users/verify-account`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
    });

    if (!response.ok) {
        const errorResponse = await response.json();
        error(400, {
                    message: errorResponse.detail
                });
    }

    const success = await response.json();
    
    return {
        message: success.message
    }
}